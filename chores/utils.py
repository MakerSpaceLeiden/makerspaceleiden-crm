from collections import defaultdict
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist

from selfservice.aggregator_adapter import get_aggregator_adapter

from .models import Chore, ChoreVolunteer


def get_chores_data(current_user_id=None, subset=None):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return None, "No aggregator configuration found"

    now = datetime.now()
    
    # Determine the start of the current week (Monday) and the end of the 2nd week
    start_of_week = now - timedelta(days=now.weekday())  # Monday
    end_of_second_week = start_of_week + timedelta(weeks=2)

    start_of_week_timestamp = start_of_week.timestamp()
    end_of_second_week_timestamp = end_of_second_week.timestamp()

    volunteers_turns = ChoreVolunteer.objects.filter(
        timestamp__gte=start_of_week_timestamp
    )
    volunteers_by_key = defaultdict(list)
    for turn in volunteers_turns:
        key = f"{turn.chore.id}-{turn.timestamp}"
        volunteers_by_key[key].append(turn.user)

    data = aggregator_adapter.get_chores()
    if data is None:
        return None, "No data available"

    event_groups = {}
    ts = None
    for event in data["events"]:
        event_ts = datetime.fromtimestamp(event["when"]["timestamp"])

        if event_ts < start_of_week or event_ts > end_of_second_week:
            continue  # Skip events outside this 2-week range

        event["time_str"] = event_ts.strftime("%H:%M")


        # Determine the start of the week (Monday)
        start_of_week = event_ts - timedelta(days=event_ts.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        week_label = f"Week Monday {start_of_week.strftime('%d-%m')} to {end_of_week.strftime('%d-%m')}"

        if week_label not in event_groups:
            event_groups[week_label] = {
                "start_date": None,
                "end_date": None,
                "events": []
            }

        if not event_groups[week_label]["start_date"]:
            event_groups[week_label]["start_date"] = start_of_week
            event_groups[week_label]["end_date"] = end_of_week

        chore_id = event["chore"]["chore_id"]
        timestamp = event["when"]["timestamp"]
        event["volunteers"] = volunteers_by_key[f"{chore_id}-{timestamp}"]
        num_missing_volunteers = event["chore"]["min_required_people"] - len(
            event["volunteers"]
        )

        if subset is not None and event["chore"]["name"] != subset:
            continue

        this_user_volunteered = current_user_id in [
            user.id for user in event["volunteers"] if hasattr(user, "id")
        ]

        # Copy the current list of volunteers
        event_volunteers = list(event["volunteers"])

        # Add the offer volunteering option first
        if num_missing_volunteers > 0 and not this_user_volunteered:
            event_volunteers.insert(0, "offer_volunteering")
            num_missing_volunteers -= 1

        # Fill remaining slots with None
        event_volunteers.extend([None] * num_missing_volunteers)

        event["volunteers"] = event_volunteers
        event["user_volunteered"] = this_user_volunteered

        try:
            chore = Chore.objects.get(id=chore_id)
            event["wiki_url"] = chore.wiki_url
        except ObjectDoesNotExist:
            event["wiki_url"] = None

        event_groups[week_label]["events"].append(event)

    if not event_groups:
        return [], "No upcoming chores available"

    # Sort weeks chronologically
    sorted_weeks = sorted(event_groups.items(), key=lambda x: x[1]["start_date"])


    return sorted_weeks, None