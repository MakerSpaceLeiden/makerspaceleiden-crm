from datetime import datetime, timedelta
from typing import TypedDict

from croniter import croniter


class EventsGenerationConfiguration(TypedDict):
    event_type: str
    starting_time: str
    crontab: str
    take_one_every: int
    duration: str | None


def _normalize_starting_time(starting_time: str) -> datetime:
    """Helper method to parse datetime string with timezone handling"""
    print("Normalizing")
    print(starting_time)
    try:
        return datetime.strptime(starting_time, "%d/%m/%Y %H:%M")
    except ValueError:
        return datetime.strptime(starting_time, "%Y/%m/%d %H:%M")


def generate_schedule_for_event(
    events_config: EventsGenerationConfiguration, number_of_days: int
) -> list[datetime]:
    crontab = events_config["crontab"]
    take_one_every = events_config["take_one_every"]
    start_time = _normalize_starting_time(events_config["starting_time"])
    print(start_time)
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

        if i % take_one_every == 0:
            # self.stdout.write(f"Next event for chore {chore}: {next}")
            schedule.append(next)

        i += 1
    return schedule
