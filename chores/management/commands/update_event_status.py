import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from agenda.models import Agenda

logger = logging.getLogger(__name__)


# Update the Event Status for any items
# created from a chore.
# For example if an event has passed but the item
# has not been completed yet the event should be
# changed to not_done
class Command(BaseCommand):
    help = "Update chore event status"

    def handle(self, *args, **options):
        self.stdout.write("Updating event status")
        events = (
            Agenda.objects.all()
            .filter(
                enddatetime__lte=timezone.now(),
                chore__isnull=False,
            )
            .exclude(status__in=["completed", "cancelled", "not_done"])
        )

        if not events.count():
            self.stdout.write("No events to update")
            logger.info("No events to update")
            return

        self.stdout.write(f"Updating {events.count()} events")
        logger.info("Updating %d events", events.count())
        for event in events:
            event.set_status("not_done", event.user)
