import logging
from datetime import datetime, timedelta, timezone

from croniter import croniter
from django.core.management.base import BaseCommand

from agenda.models import Agenda

from ...models import Chore

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
            self.stdout.write(
                f"Generating events for chore {chore} {chore.configuration['events_generation']['crontab']}"
            )

            crontab = chore.configuration["events_generation"]["crontab"]
            weekly_frequency = chore.configuration["events_generation"][
                "take_one_every"
            ]

            cron = croniter(
                crontab,
                datetime.now(),
            )
            limit = datetime.now() + timedelta(days=number_of_days)

            i = 0
            while True:
                next = cron.get_next(datetime)
                if next:
                    if next > limit:
                        self.stdout.write(f"Reached limit for chore {chore}")
                        break

                    if i % weekly_frequency == 0:
                        self.stdout.write(f"Next event for chore {chore}: {next}")
                        self.create_event(chore, next)

                    i += 1
                else:
                    self.stdout.write(f"No more events for chore {chore}")
                    break

    def create_event(self, chore, next):
        # Query first by chore.name + _startdatetime
        # If not found, create new
        if not Agenda.objects.filter(
            chore=chore,
            _startdatetime=next.astimezone(timezone.utc),
        ).exists():
            agenda = Agenda.objects.create(
                item_title=chore.name,
                item_details=chore.description,
                _startdatetime=next.astimezone(timezone.utc),
                user=chore.creator,
                chore=chore,
            )
            logger.debug("Created agenda", agenda)
        else:
            logger.debug("Found existing agenda item.")
