import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from .core import ChoreEventsLogic, Time
from .models import Chore, ChoreVolunteer

logger = logging.getLogger(__name__)

NUMBER_OF_DAYS_AHEAD = 90


def chores_get_all_from(now):
    then = now + (NUMBER_OF_DAYS_AHEAD * 24 * 60 * 60)  # Add 14 days
    chores = Chore.objects.all()
    data = ChoreEventsLogic(chores).get_events_from_to(
        Time.from_timestamp(now), Time.from_timestamp(then)
    )
    return [e.for_json() for e in data]


def getall(current_user_id=None, subset=None):
    now = time.time()
    volunteers_turns = ChoreVolunteer.objects.filter(timestamp__gte=now)
    volunteers_by_key = defaultdict(list)
    for turn in volunteers_turns:
        key = f"{turn.chore.id}-{turn.timestamp}"
        volunteers_by_key[key].append(turn.user)

    # FIXME: replace use of aggregator_adapter.get_chores()
    data = chores_get_all_from(now)

    event_groups = []
    ts = None
    if data is not None:
        for event in data:
            event_ts = datetime.fromtimestamp(event["when"]["timestamp"])
            event_ts_str = event_ts.strftime("%d%m%Y")
            event["time_str"] = event_ts.strftime("%H:%M")
            chore_id = event["chore"]["chore_id"]
            timestamp = event["when"]["timestamp"]
            event["volunteers"] = volunteers_by_key[f"{chore_id}-{timestamp}"]
            num_missing_volunteers = event["chore"]["min_required_people"] - len(
                event["volunteers"]
            )
            if subset is not None and not event["chore"]["name"] == subset:
                continue
            this_user_volunteered = current_user_id in [
                user.id for user in event["volunteers"] if hasattr(user, "id")
            ]
            if num_missing_volunteers > 0:
                for idx in range(num_missing_volunteers):
                    if idx == 0 and not this_user_volunteered:
                        event["volunteers"].append("offer_volunteering")
                    else:
                        event["volunteers"].append(None)
            event["volunteers"] = [str(n) for n in event["volunteers"]]

            if event_ts_str != ts:
                ts = event_ts_str
                event_groups.append(
                    {
                        "ts_str": event_ts.strftime("%A %d/%m/%Y"),
                        "timestamp": timestamp,
                        "events": [],
                    }
                )

            try:
                chore = Chore.objects.get(id=chore_id)
                event["wiki_url"] = chore.wiki_url
            except ObjectDoesNotExist:
                event["wiki_url"] = None

            event_groups[-1]["events"].append(event)

    return sorted(event_groups, key=lambda e: e["timestamp"])


def index_api(request, name=None):
    chores = getall(None, name)

    if not chores:
        return HttpResponse("No chores found", status=404, content_type="text/plain")

    payload = {
        "title": "Chores of this week",
        "version": "1.00",
        "chores": chores,
    }
    if name:
        payload["title"] = name

    js = json.dumps(payload).encode("utf8")
    return HttpResponse(js, content_type="application/json")


@login_required
def index(request):
    chores_data = []

    chores_data, error_message = get_chores_overview(current_user_id=request.user.id)

    context = {
        "title": "Chores",
        "event_groups": chores_data if chores_data else [],
        "has_permission": request.user.is_authenticated,
        "user": request.user,
    }
    return render(request, "chores.html", context)


def get_chores_overview(current_user_id=None, subset=None):
    now = time.time()

    volunteers_turns = ChoreVolunteer.objects.all()
    volunteers_by_key = defaultdict(list)
    for turn in volunteers_turns:
        key = f"{turn.chore.id}-{turn.timestamp}"
        volunteers_by_key[key].append(turn.user)

    chore_events = chores_get_all_from(now)
    if chore_events is None:
        return None, "No data available"

    event_groups = {}

    for event in chore_events:
        event_ts = datetime.fromtimestamp(event["when"]["timestamp"])

        event["time_str"] = event_ts.strftime("%H:%M")

        # Determine the start of the week (Monday)
        start_of_week = event_ts - timedelta(days=event_ts.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        week_label = f"Week Monday {start_of_week.strftime('%d-%m')} to {end_of_week.strftime('%d-%m')}"

        if week_label not in event_groups:
            event_groups[week_label] = {
                "start_date": None,
                "end_date": None,
                "events": [],
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


@login_required
def signup(request, chore_id, ts):
    try:
        chore = Chore.objects.get(pk=chore_id)
    except ObjectDoesNotExist:
        return HttpResponse("Chore not found", status=404, content_type="text/plain")

    try:
        ChoreVolunteer.objects.create(user=request.user, chore=chore, timestamp=ts)
    except Exception as e:
        logger.error("Something else went wrong during create: {0}".format(e))
        raise e
    try:
        context = {"chore": chore, "volunteer": request.user}
        subject = render_to_string("notify_email.subject.txt", context).strip()
        body = render_to_string("notify_email.txt", context)

        EmailMessage(
            subject,
            body,
            to=[request.user.email, settings.MAILINGLIST],
            from_email=settings.DEFAULT_FROM_EMAIL,
        ).send()
    except Exception as e:
        logger.error("Something else went wrong during mail sent: {0}".format(e))

    redirect_to = request.GET.get("redirect_to", "chores")

    return redirect(redirect_to)


@login_required
def remove_signup(request, chore_id, ts):
    try:
        chore = Chore.objects.get(pk=chore_id)
    except ObjectDoesNotExist:
        return HttpResponse("Chore not found", status=404, content_type="text/plain")

    try:
        ChoreVolunteer.objects.filter(
            user=request.user, chore=chore, timestamp=ts
        ).delete()
    except Exception as e:
        logger.error("Something else went wrong during delete: {0}".format(e))
        raise e
    try:
        context = {"chore": chore, "volunteer": request.user}
        subject = render_to_string("notify_email_nope.subject.txt", context).strip()
        body = render_to_string("notify_email_nope.txt", context)

        EmailMessage(
            subject,
            body,
            to=[request.user.email, settings.MAILINGLIST],
            from_email=settings.DEFAULT_FROM_EMAIL,
        ).send()
    except Exception as e:
        logger.error("Something else went wrong during remove mail sent: {0}".format(e))

    redirect_to = request.GET.get("redirect_to", "chores")

    return redirect(redirect_to)
