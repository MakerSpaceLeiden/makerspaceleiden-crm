import logging
from collections import namedtuple
from datetime import datetime

from django.core.management.base import BaseCommand

from ...core import ChoreEventsLogic, Time
from ...models import Chore, ChoreVolunteer

logger = logging.getLogger(__name__)


NudgesParams = namedtuple(
    "NudgesParams", "volunteers now urls message_users_seen_no_later_than_days"
)


class Clock(object):
    @staticmethod
    def now():
        return Time.from_datetime(datetime.utcnow())


class Command(BaseCommand):
    help = "Send reminders for chores"

    def handle(self, *args, **kwargs):
        chores = Chore.objects.all()
        logger.debug("handle", len(chores))
        now = Clock.now()

        # Configuration lifted from aggregator
        # TODO: Make these configurable
        self.chores_warnings_check_window_in_hours = 2
        self.chores_message_users_seen_no_later_than_days = 14

        for event in ChoreEventsLogic(chores).iter_events_with_reminders_from_to(
            now.add(-self.chores_warnings_check_window_in_hours, "hours"), now
        ):
            volunteers = ChoreVolunteer.objects.all().filter(chore=event.chore.chore_id)
            logger.debug("send_reminders.handle.volunteers", len(volunteers))
            params = NudgesParams(
                volunteers,
                now,
                Urls(),
                self.chores_message_users_seen_no_later_than_days,
            )
            for nudge in event.iter_nudges(params):
                logger.info("Processing Chore nudge: {0}".format(nudge))
                logger.debug("nudge.get_string_key", nudge.get_string_key())
                nudge.send()

        self.stdout.write("Sending notifications")


class Urls(object):
    def notification_settings(self):
        return "https://mijn.makerspaceleiden.nl/notifications/settings"

    def space_state(self):
        return "https://mijn.makerspaceleiden.nl/space_state"

    def chores(self):
        return "https://mijn.makerspaceleiden.nl/chores/"
