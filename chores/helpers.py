from isodate import parse_duration
from datetime import datetime, timedelta, timezone
from datetime import datetime, timedelta

from agenda.models import Agenda

def _get_chore_enddatetime(next, chore_configuration) -> datetime:
    events_generation = chore_configuration.get("events_generation", {})
    duration = events_generation.get("duration")
    if not duration:
        return (next + timedelta(days=7)).astimezone(timezone.utc)
    return (next + parse_duration(duration)).astimezone(timezone.utc)

def create_chore_agenda_item(chore, next: datetime, logger = None) -> bool:
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
        return True
    else:
        logger.debug("Found existing agenda item.")
        return False
