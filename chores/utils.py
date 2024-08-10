from collections import defaultdict
from datetime import datetime, timedelta
import time
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

from selfservice.aggregator_adapter import get_aggregator_adapter
from .models import Chore, ChoreVolunteer


def get_chores_data(current_user_id=None, subset=None):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return None, "No aggregator configuration found"

    now = datetime.now()
    three_weeks_from_now = now + timedelta(weeks=2)  # Current time + 3 weeks

    now_timestamp = now.timestamp()
    three_weeks_from_now_timestamp = three_weeks_from_now.timestamp()

    volunteers_turns = ChoreVolunteer.objects.filter(timestamp__gte=now_timestamp)
    volunteers_by_key = defaultdict(list)
    for turn in volunteers_turns:
        key = f"{turn.chore.id}-{turn.timestamp}"
        volunteers_by_key[key].append(turn.user)

    data = aggregator_adapter.get_chores()
    if data is None:
        return None, "No data available"

    event_groups = []
    ts = None
    for event in data["events"]:
        event_ts = datetime.fromtimestamp(event["when"]["timestamp"])
        if event_ts < now or event_ts > three_weeks_from_now:
            continue  # Skip events outside the range

        event_ts_str = event_ts.strftime("%A, %d-%m")
        event["time_str"] = event_ts.strftime("%H:%M")
        chore_id = event["chore"]["chore_id"]
        timestamp = event["when"]["timestamp"]
        event["volunteers"] = volunteers_by_key[f"{chore_id}-{timestamp}"]
        num_missing_volunteers = event["chore"]["min_required_people"] - len(event["volunteers"])

        if subset is not None and event["chore"]["name"] != subset:
            continue
        
        this_user_volunteered = current_user_id in [user.id for user in event["volunteers"] if hasattr(user, 'id')]
        
        # Copy the current list of volunteers
        event_volunteers = list(event["volunteers"])  
        
        # Add the offer volunteering option first
        if num_missing_volunteers > 0 and not this_user_volunteered:
            event_volunteers.insert(0, 'offer_volunteering')  
            num_missing_volunteers -= 1

        # Fill remaining slots with None
        event_volunteers.extend([None] * num_missing_volunteers)  

        event["volunteers"] = event_volunteers
        event["user_volunteered"] = this_user_volunteered

        if event_ts_str != ts:
            ts = event_ts_str
            event_groups.append({
                "ts_str": event_ts_str,
                "timestamp": timestamp,
                "events": [],
            })

        try:
            chore = Chore.objects.get(id=chore_id)
            event["wiki_url"] = chore.wiki_url
        except ObjectDoesNotExist:
            event["wiki_url"] = None

        event_groups[-1]["events"].append(event)
    
    return sorted(event_groups, key=lambda e: e["timestamp"]), None