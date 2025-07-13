import logging
from datetime import datetime, timedelta, timezone
from dateutil.tz import tzlocal
from .messages import VolunteeringReminderNotification
from functools import total_ordering
from django.core.mail import EmailMessage
from .models import Chore, ChoreNotification

import humanize
from croniter import croniter
logger = logging.getLogger(__name__)

HUMAN_DATETIME_STRING = "%H:%M:%S %d/%m/%Y"
local_timezone = tzlocal()

class BaseNudge(object):
    """Base class for all nudge types with common functionality."""

    def __init__(self, event):
        self.event = event

    def get_string_key(self):
        """Generate a unique string key for this nudge."""
        event_key = self.event.get_object_key()
        return "{0}-{1}-{2}".format(
            self.nudge_key, event_key["chore_id"], event_key["ts"]
        )

    def send(self):
        """Send the nudge - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement send()")

    def should_send(self, message_key):
        """Check if a message with this key should be sent (not already sent)."""
        return not ChoreNotification.objects.filter(event_key=message_key).exists()

    def record_send(self, message_key, user=None):
        """Record that a message with this key has been sent."""
        ChoreNotification.objects.create(
            event_key=message_key,
            chore=Chore.objects.get(id=self.event.get_object_key()["chore_id"]),
            recipient_user=user if "volunteer" in message_key else None,
            recipient_other=None
            if "volunteer" in message_key
            else "deelnemers@makerspaceleiden.nl",
        )


class EmailNudge(BaseNudge):
    def __init__(self, event, nudge_key, destination, subject, body):
        super().__init__(event)
        self.nudge_key = nudge_key
        self.destination = destination
        self.subject = subject
        self.body = body

    def __str__(self):
        return "Email nudge. Chore: {0}, to: {1}, subject: {2}".format(
            self.event.chore.name, self.destination, self.subject
        )

    def send(self):
        logger.info("Sending email nudge to: {0}".format(self.destination))
        logger.debug("EmailNudge.send", self.destination)

        if self.should_send(self.get_string_key()):
            EmailMessage(
                self.subject,
                self.body,
                to=[self.destination],
                from_email="MakerSpace BOT <noc@makerspaceleiden.nl>",
            ).send()
            self.record_send(self.get_string_key())

    # Honour the Message API (see messages.py)
    def get_subject_for_email(self):
        return self.subject

    # Honour the Message API (see messages.py)
    def get_email_text(self):
        return self.body + "\n"


class VolunteersReminderNudge(BaseNudge):
    def __init__(self, event, params):
        super().__init__(event)
        self.volunteers = params.volunteers
        self.nudge_key = "volunteer-reminder"

    def __str__(self):
        return "Volunteer reminder via Chat BOT: {0}".format(self.event.chore.name)

    def send(self):
        logger.debug("VolunteersReminderNudge.Send", len(self.volunteers))
        logger.info(
            "Sending volunteering reminder to: {0}".format(
                ", ".join(["{0}".format(u.full_name) for u in self.volunteers])
            )
        )
        for choreVolunteer in self.volunteers:
            notification_key = self.get_string_key() + "-{0}".format(
                choreVolunteer.user.id
            )
            if self.should_send(notification_key):
                logger.debug(
                    "aggregator.send_user_notification.{0}".format(choreVolunteer.user)
                )
                message = VolunteeringReminderNotification(
                    choreVolunteer.user, self.event
                )
                EmailMessage(
                    message.get_subject_for_email(),
                    message.get_text(),
                    to=[choreVolunteer.user.email],
                    from_email="MakerSpace BOT <noc@makerspaceleiden.nl>",
                ).send()
                self.record_send(notification_key, choreVolunteer.user)


class ChoreEventsLogic(object):
    def __init__(self, chores):
        self.chores = [build_chore_instance(chore) for chore in chores]

    def get_events_from_to(self, ts_from, ts_to):
        events = []
        for chore in self.chores:
            events.extend(chore.iter_events_from_to(ts_from, ts_to))

        events.sort(key=lambda c: c.ts)
        return events

    def iter_events_with_reminders_from_to(self, ts_from, ts_to):
        logger.debug("iter_events_with_reminders_from_to", ts_from, ts_to)
        num_days_of_earliest_reminder = max(
            [0] + [chore.get_num_days_of_earliest_reminder() for chore in self.chores]
        )
        for event in self.get_events_from_to(
            ts_from, ts_to.add(num_days_of_earliest_reminder + 1, "days")
        ):
            logger.debug("get_events_from_to.event", event)
            for reminder in event.chore.reminders:
                logger.debug("event.chore.reminders", reminder)
                reminder_time = calculate_reminder_time(event, reminder.when)
                if ts_from <= reminder_time <= ts_to:
                    yield event


class ChoreEvent(object):
    def __init__(self, chore, ts):
        self.chore = chore
        self.ts = ts

    def get_object_key(self):
        return {
            "chore_id": self.chore.chore_id,
            "ts": self.ts.as_int_timestamp(),
        }

    def for_json(self):
        return {
            "chore": self.chore.for_json(),
            "when": {
                "timestamp": self.ts.as_int_timestamp(),
                "human_str": self.ts.human_str(),
            },
        }

    def iter_nudges(self, params):
        for reminder in self.chore.reminders:
            for nudge in reminder.iter_nudges(self, params):
                yield nudge


class BasicChore(object):
    def __init__(
        self,
        chore_id,
        name,
        description,
        min_required_people,
        events_generation,
        reminders,
    ):
        self.chore_id = chore_id
        self.name = name
        self.description = description
        self.min_required_people = min_required_people

        self.events_generator = None
        event_type = events_generation["event_type"]
        data = dict(events_generation)
        del data["event_type"]
        if event_type == "recurrent":
            self.events_generator = RecurrentEventGenerator(**data)
        elif event_type == "single_occurrence":
            self.events_generator = SingleOccurrenceEventGenerator(**data)

        self.reminders = [
            build_reminder(self.min_required_people, **reminder)
            for reminder in reminders
        ]

    def iter_events_from_to(self, ts_from, ts_to):
        """
        Yield events generated by the events_generator between two timestamps.

        Args:
            ts_from (int): The start timestamp (inclusive).
            ts_to (int): The end timestamp (inclusive).

        Yields:
            event: Each event generated by the events_generator within the given range.
        """
        if self.events_generator:
            for event in self.events_generator.iter_events_from_to(
                self, ts_from, ts_to
            ):
                yield event

    def for_json(self):
        return {
            "chore_id": self.chore_id,
            "name": self.name,
            "description": self.description,
            "min_required_people": self.min_required_people,
        }

    def get_num_days_of_earliest_reminder(self):
        return max([0] + [reminder.when["days_before"] for reminder in self.reminders])



class RecurrentEventGenerator(object):
    def __init__(self, starting_time, crontab, take_one_every):
        self.starting_time = Time.from_datetime(
            datetime.strptime(starting_time, "%d/%m/%Y %H:%M")
        )
        self.crontab = crontab
        self.take_one_every = take_one_every

    def iter_events_from_to(self, aggregator, ts_from, ts_to):
        for idx, ts in enumerate(Time.iter_crontab(self.crontab, self.starting_time)):
            if ts > ts_to:
                break
            if ts >= ts_from and idx % self.take_one_every == 0:
                yield ChoreEvent(aggregator, ts)


class SingleOccurrenceEventGenerator(object):
    def __init__(self, event_time):
        self.event_time = Time.from_datetime(
            datetime.strptime(event_time, "%d/%m/%Y %H:%M")
        )

    def iter_events_from_to(self, aggregator, ts_from, ts_to):
        if ts_from <= self.event_time <= ts_to:
            yield ChoreEvent(aggregator, self.event_time)





ALL_CHORE_TYPES = [
    BasicChore,
]


class MissingVolunteersReminder(object):
    def __init__(self, min_required_people, when, nudges):
        self.min_required_people = min_required_people
        self.when = when
        self.nudges = nudges

    def iter_nudges(self, event, params):
        reminder_time = calculate_reminder_time(event, self.when)
        if params.now > reminder_time and len(params.volunteers) == 0:
            for nudge in self.nudges:
                if nudge["nudge_type"] == "email":
                    yield self._build_email_nudge(event, nudge, params)
                else:
                    logger.warn("Unsupported nudge type", nudge["nudge_type"])

    def _build_email_nudge(self, event, nudge, params):
        template_data = {
            "event_day": event.ts.strftime("%a %d/%m/%Y %H:%M"),
            "chore_description": event.chore.description,
            "num_volunteers_needed": self.min_required_people - len(params.volunteers),
            "signup_url": params.urls.chores(),
        }
        return EmailNudge(
            event=event,
            nudge_key=nudge["nudge_key"],
            destination=nudge["destination"],
            subject=nudge["subject_template"].format(**template_data),
            body=nudge["body_template"].format(**template_data),
        )


class VolunteersReminder(object):
    def __init__(self, when):
        self.when = when

    def iter_nudges(self, event, params):
        reminder_time = calculate_reminder_time(event, self.when)
        if params.now > reminder_time:
            yield VolunteersReminderNudge(event, params)


def build_reminder(min_required_people, reminder_type, when, nudges=None):
    logger.debug("build_reminder", reminder_type, when)
    if reminder_type == "missing_volunteers":
        return MissingVolunteersReminder(min_required_people, when, nudges)
    if reminder_type == "volunteers_who_signed_up":
        return VolunteersReminder(when)
    raise Exception(f"Unknown reminder type {repr(reminder_type)}")


def get_chore_type_class(chore):
    for chore_class in ALL_CHORE_TYPES:
        if chore_class.__name__ == chore.class_type:
            return chore_class
    raise Exception(f'Cannot find Python class for chore of type "{chore.class_type}"')

def build_chore_instance(chore):
    chore_class = get_chore_type_class(chore)
    return chore_class(chore.id, chore.name, chore.description, **chore.configuration)


def parse_hhmm(hhmm_str):
    hh, mm = hhmm_str.split(":")
    return int(hh), int(mm)


def calculate_reminder_time(event, when):
    logger.debug("calculate_reminder_time", event, when)
    hh, mm = parse_hhmm(when["time"])
    reminder_time = event.ts.add(-when["days_before"], "days").replace(
        hour=hh, minute=mm
    )
    return reminder_time

@total_ordering
class Time(object):
    # Internally represents time in UTC
    # The internal instance of datetime object is naive, i.e. without timezone information

    def __init__(self, dt):
        self.dt = dt

    def __repr__(self):
        return f"<Time {self.human_str()}>"

    def __eq__(self, other):
        return self.dt == other.dt

    def __ne__(self, other):
        return self.dt != other.dt

    def __lt__(self, other):
        return self.dt < other.dt

    def __hash__(self):
        return hash(self.dt)

    def as_int_timestamp(self):
        return int(self.dt.replace(tzinfo=timezone.utc).timestamp())

    def sorting_key(self):
        return self.as_int_timestamp()

    def replace(self, hour=None, minute=None):
        return Time(self.dt.replace(hour=hour, minute=minute, second=0))

    @classmethod
    def from_timestamp(cls, ts):
        return cls(datetime.utcfromtimestamp(ts))

    @classmethod
    def from_datetime(cls, dt):
        return cls(dt)

    def human_str(self):
        return self.strftime(HUMAN_DATETIME_STRING)

    def strftime(self, _format):
        return (
            self.dt.replace(tzinfo=timezone.utc)
            .astimezone(local_timezone)
            .strftime(_format)
        )

    def human_delta_from(self, ts_from):
        delta = (self.dt - ts_from.dt).total_seconds()
        return humanize.naturaldelta(delta) + " ago"

    def delta_in_hours(self, ts_from):
        return (self.dt - ts_from.dt).total_seconds() / 3600

    def add(self, how_much, what):
        if what in ("minute", "minutes"):
            return Time(self.dt + timedelta(minutes=how_much))
        if what in ("hour", "hours"):
            return Time(self.dt + timedelta(hours=how_much))
        if what in ("day", "days"):
            return Time(self.dt + timedelta(days=how_much))

    @classmethod
    def iter_crontab(cls, crontab, starting_ts):
        croniter_iterator = croniter(crontab, starting_ts.dt)
        while True:
            dt = (
                croniter_iterator.get_next(datetime)
                .replace(tzinfo=local_timezone)
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )
            yield cls.from_datetime(dt)
