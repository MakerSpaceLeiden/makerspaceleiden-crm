import logging
from datetime import datetime, timedelta, timezone
from typing import TypedDict

from croniter import croniter
from django.core.management.base import BaseCommand
from isodate import parse_duration

from agenda.models import Agenda

from ...models import Chore

logger = logging.getLogger(__name__)


class EventsGenerationConfiguration(TypedDict):
    event_type: str
    starting_time: str
    crontab: str
    take_one_every: int
    duration: str | None


def generate_schedule_for_event(
    events_config: EventsGenerationConfiguration, number_of_days: int
) -> list[datetime]:
    crontab = events_config["crontab"]
    weekly_frequency = events_config["take_one_every"]
    start_time = datetime.strptime(events_config["starting_time"], "%d/%m/%Y %H:%M")
    cron = croniter(
        crontab,
        start_time,
    )
    limit = datetime.now() + timedelta(days=number_of_days)

    schedule = []

    i = 0
    while True:
        next = cron.get_next(datetime)
        if next > limit:
            # self.stdout.write(f"Reached limit for chore {chore}")
            break

        if next < datetime.now():
            i += 1
            continue

        if i % weekly_frequency == 0:
            # self.stdout.write(f"Next event for chore {chore}: {next}")
            schedule.append(next)

        i += 1
    return schedule


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
                self.create_event(chore, next)

    def create_event(self, chore, next):
        # Query first by chore.name + startdatetime
        # If not found, create new
        if not Agenda.objects.filter(
            chore=chore,
            startdatetime=next.astimezone(timezone.utc),
        ).exists():
            end_datetime = _get_chore_enddatetime(next, chore.configuration)

            agenda = Agenda.objects.create(
                item_title=chore.name.replace("_", " ").title(),
                item_details=chore.description,
                startdatetime=next.astimezone(timezone.utc),
                enddatetime=end_datetime,
                user=chore.creator,
                chore=chore,
            )
            logger.debug("Created agenda", agenda)
        else:
            logger.debug("Found existing agenda item.")


def _get_chore_enddatetime(next, chore_configuration) -> datetime:
    events_generation = chore_configuration.get("events_generation", {})
    duration = events_generation.get("duration")
    if not duration:
        return (next + timedelta(days=7)).astimezone(timezone.utc)
    return (next + parse_duration(duration)).astimezone(timezone.utc)
