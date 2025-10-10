import logging

from django.core.management.base import BaseCommand

from ...helpers import create_chore_agenda_item
from ...models import Chore
from ...schedule import generate_schedule_for_event

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate events for chores"

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=14,
            help="Limit the number of days to generate events for",
        )

    def handle(self, *args, **options):
        chores = Chore.objects.all()
        logger.debug("handle", len(chores))

        # TODO: Limit window of time to generate events for
        number_of_days = options["limit"]

        self.stdout.write(
            f"Generating events for chores over next {number_of_days} days"
        )
        for chore in chores:
            logger.debug("Generating events for chore", chore)
            events_config = chore.configuration["events_generation"]
            if not events_config["event_type"] == "recurrent":
                self.stdout.write(
                    f"Unsupported event_type {events_config['event_type']}"
                )
                continue

            self.stdout.write(
                f"Generating events for chore {chore} {chore.configuration['events_generation']['crontab']}"
            )

            schedule = generate_schedule_for_event(events_config, number_of_days)

            for next in schedule:
                create_chore_agenda_item(chore, next, logger)
