import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from agenda.models import Agenda

logger = logging.getLogger(__name__)


# Update the Event Status for any items created
# from a chore
# For example if an event has passed but the item
# has not been completed yet the event should be
# changed to not_done
class Command(BaseCommand):
    help = "Update chore event status"

    def handle(self, *args, **options):
        events = (
            Agenda.objects.all()
            .filter(enddatetime__lte=timezone.now())
            .exclude(status__in=["completed", "cancelled", "not_done"])
        )

        for event in events:
            event.set_status("not_done", event.user)
