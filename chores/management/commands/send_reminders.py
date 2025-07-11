import logging
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from functools import total_ordering

import humanize
from croniter import croniter
from dateutil.tz import tzlocal
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand

from ...models import Chore, ChoreNotification, ChoreVolunteer

logger = logging.getLogger(__name__)

HUMAN_DATETIME_STRING = "%H:%M:%S %d/%m/%Y"
local_timezone = tzlocal()

NudgesParams = namedtuple(
    "NudgesParams", "volunteers now urls message_users_seen_no_later_than_days"
)


class Command(BaseCommand):
    help = "Send reminders for chores"

    def handle(self, *args, **kwargs):
        chores = Chore.objects.all()
        print("LADEBUG.handle", len(chores))
        chores_logic = ChoresLogic(chores)
        now = Clock.now()
        events = chores_logic.get_events_from_to(now, now.add(90, "days"))

        print("event count:")
        print(len(events))

        # Configuration lifted from aggregator
        self.chores_warnings_check_window_in_hours = 2
        self.chores_message_users_seen_no_later_than_days = 14

        for event in chores_logic.iter_events_with_reminders_from_to(
            now.add(-self.chores_warnings_check_window_in_hours, "hours"), now
        ):
            volunteers = ChoreVolunteer.objects.all()
            params = NudgesParams(
                volunteers,
                now,
                Urls(),
                self.chores_message_users_seen_no_later_than_days,
            )
            for nudge in event.iter_nudges(params):
                logger.info("Processing Chore nudge: {0}".format(nudge))
                print("LADEBUG.Processing Chore nudge: {0}".format(nudge))
                # Prevent multiple notifications using ChoreNotification
                print("LADEBUG.nudge.get_string_key", nudge.get_string_key())
                event_key = nudge.get_string_key()
                exists = ChoreNotification.objects.filter(event_key=event_key).exists()
                if not exists:
                    nudge.send(self, logger)
                    # send and create notification
                    ChoreNotification.objects.create(
                        event_key=nudge.get_string_key(),
                        chore=Chore.objects.get(id=event.get_object_key()["chore_id"]),
                        recipient_user=None,
                        recipient_other="deelnemers@makerspaceleiden.nl",  # LADEBUG.FIXME
                    )
                else:
                    logger.info(
                        f"Skipping duplicate notification for event_key={event_key}"
                    )

        self.stdout.write("Sending notifications")


class Urls(object):
    def notification_settings(self):
        return "https://mijn.makerspaceleiden.nl/notifications/settings"

    def space_state(self):
        return "https://mijn.makerspaceleiden.nl/space_state"

    def chores(self):
        return "https://mijn.makerspaceleiden.nl/chores/"


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


ALL_CHORE_TYPES = [
    BasicChore,
]


class EmailNudge(object):
    def __init__(self, event, nudge_key, destination, subject, body):
        self.event = event
        self.nudge_key = nudge_key
        self.destination = destination
        self.subject = subject
        self.body = body

    def __str__(self):
        return "Email nudge. Chore: {0}, to: {1}, subject: {2}".format(
            self.event.chore.name, self.destination, self.subject
        )

    def get_string_key(self):
        event_key = self.event.get_object_key()
        return "{0}-{1}-{2}".format(
            self.nudge_key, event_key["chore_id"], event_key["ts"]
        )

    def send(self, aggregator, logger):
        logger.info("Sending email nudge to: {0}".format(self.destination))
        print("LADEBUG.EmailNudge.send", self.destination)

        EmailMessage(
            self.subject,
            self.body,
            to=[self.destination],
            from_email="MakerSpace BOT <noc@makerspaceleiden.nl>",
        ).send()

        # TODO: LADEBUG send email (1)
        # aggregator.email_adapter.send_email(
        #     self.destination, self.destination, self, logger
        # )

    # Honour the Message API (see messages.py)
    def get_subject_for_email(self):
        return self.subject

    # Honour the Message API (see messages.py)
    def get_email_text(self):
        return self.body + "\n"


class VolunteerViaChatBotNudge(object):
    def __init__(self, event, nudge, params):
        self.event = event
        self.nudge = nudge
        self.message_users_seen_no_later_than_days = (
            params.message_users_seen_no_later_than_days
        )
        self.urls = params.urls

    def __str__(self):
        return "Chat BOT nudge: {0}".format(self.event.chore.name)

    def get_string_key(self):
        event_key = self.event.get_object_key()
        return "{0}-{1}-{2}".format(
            self.nudge["nudge_key"], event_key["chore_id"], event_key["ts"]
        )

    def send(self, aggregator, logger):
        users = aggregator.get_users_seen_no_later_than_days(
            self.message_users_seen_no_later_than_days, logger
        )
        logger.info(
            "Sending Chat BOT nudge to: {0}".format(
                ", ".join(["{0}".format(u.full_name) for u in users])
            )
        )
        for user in users:
            print(user)
            # aggregator.send_user_notification(
            #     user,
            #     AskForVolunteeringNotification(user, self.event, self.urls),
            #     logger,
            # )


class VolunteerReminderViaChatBotNudge(object):
    def __init__(self, event, params):
        self.event = event
        self.volunteers = params.volunteers

    def __str__(self):
        return "Volunteer reminder via Chat BOT: {0}".format(self.event.chore.name)

    def get_string_key(self):
        event_key = self.event.get_object_key()
        return "volunteer-reminder-{0}-{1}".format(
            event_key["chore_id"], event_key["ts"]
        )

    def send(self, aggregator, _logger):
        print("LADEBUG.VolunteerReminderViaChatBotNudge.Send")
        logger.info(
            "Sending volunteering reminder to: {0}".format(
                ", ".join(["{0}".format(u.full_name) for u in self.volunteers])
            )
        )
        for user in self.volunteers:
            print("aggregator.send_user_notification")
            print(user)
            # aggregator.send_user_notification(
            #     user, VolunteeringReminderNotification(user, self.event), logger
            # )


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
                if nudge["nudge_type"] == "volunteer_via_chat_bot":
                    yield VolunteerViaChatBotNudge(event, nudge, params)

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
            yield VolunteerReminderViaChatBotNudge(event, params)


class ChoresLogic(object):
    def __init__(self, chores):
        self.chores = [build_chore_instance(chore) for chore in chores]

    def get_events_from_to(self, ts_from, ts_to):
        events = []
        for chore in self.chores:
            print("LADEBUG:chore", ts_from, ts_to)
            events.extend(chore.iter_events_from_to(ts_from, ts_to))
            print("LADEBUG:Events.after", len(events))

        events.sort(key=lambda c: c.ts)
        return events

    def iter_events_with_reminders_from_to(self, ts_from, ts_to):
        print("LADEBUG.iter_events_with_reminders_from_to", ts_from, ts_to)
        num_days_of_earliest_reminder = max(
            [0] + [chore.get_num_days_of_earliest_reminder() for chore in self.chores]
        )
        for event in self.get_events_from_to(
            ts_from, ts_to.add(num_days_of_earliest_reminder + 1, "days")
        ):
            print("LADEBUG.get_events_from_to.event", event)
            for reminder in event.chore.reminders:
                print("LADEBUG.event.chore.reminders", reminder)
                reminder_time = calculate_reminder_time(event, reminder.when)
                print(
                    "LADEBUG.event.chore.reminders.yield?",
                    {
                        "ts_from": ts_from,
                        "reminder_time": reminder_time,
                        "ts_to": ts_to,
                        "test": ts_from <= reminder_time <= ts_to,
                    },
                )
                if ts_from <= reminder_time <= ts_to:
                    yield event


# -- Utility functions ----


def get_chore_type_class(chore):
    for chore_class in ALL_CHORE_TYPES:
        if chore_class.__name__ == chore.class_type:
            return chore_class
    raise Exception(f'Cannot find Python class for chore of type "{chore.class_type}"')


def build_chore_instance(chore):
    chore_class = get_chore_type_class(chore)
    return chore_class(chore.id, chore.name, chore.description, **chore.configuration)


def build_reminder(min_required_people, reminder_type, when, nudges=None):
    if reminder_type == "missing_volunteers":
        return MissingVolunteersReminder(min_required_people, when, nudges)
    if reminder_type == "volunteers_who_signed_up":
        return VolunteersReminder(when)
    raise Exception(f"Unknown reminder type {repr(reminder_type)}")


def parse_hhmm(hhmm_str):
    hh, mm = hhmm_str.split(":")
    return int(hh), int(mm)


def calculate_reminder_time(event, when):
    print("LADEBUG.calculate_reminder_time", event, when)
    hh, mm = parse_hhmm(when["time"])
    reminder_time = event.ts.add(-when["days_before"], "days").replace(
        hour=hh, minute=mm
    )
    return reminder_time


class Clock(object):
    @staticmethod
    def now():
        return Time.from_datetime(datetime.utcnow())


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
