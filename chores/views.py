import json
import logging
import time
from collections import defaultdict

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from agenda.models import Agenda

from .models import Chore, ChoreVolunteer

logger = logging.getLogger(__name__)


def getall(current_user_id=None, subset=None):
    now = time.time()
    volunteers_turns = ChoreVolunteer.objects.filter(timestamp__gte=now)
    volunteers_by_key = defaultdict(list)
    for turn in volunteers_turns:
        key = f"{turn.chore.id}-{turn.timestamp}"
        volunteers_by_key[key].append(turn.user)

    events = Agenda.objects.upcoming()
    event_groups = []
    ts = None
    for event in events:
        event_ts = event.start_datetime
        event_ts_str = event_ts.strftime("%d%m%Y")
        if event_ts_str != ts:
            ts = event_ts_str
            event_groups.append(
                {
                    "ts_str": event_ts.strftime("%A %d/%m/%Y"),
                    "timestamp": event_ts,
                    "events": [],
                }
            )

        # FIXIME event["wiki_url"] = None
        event_groups[-1]["events"].append(event)

    return sorted(event_groups, key=lambda e: e["timestamp"])


def index_api(request, name=None):
    chores = getall(None, name)

    if not chores:
        return HttpResponse("No chores found", status=404, content_type="text/plain")
    payload = {
        "title": "Chores of this week",
        "version": "1.00",
        "chores": list(map(lambda x: {"title": "foo"}, chores)),
    }
    if name:
        payload["title"] = name

    js = json.dumps(payload).encode("utf8")
    return HttpResponse(js, content_type="application/json")


@login_required
def index(request):
    context = {
        "title": "Chores",
        "chores": Agenda.objects.upcoming_chores(),
        "has_permission": request.user.is_authenticated,
        "user": request.user,
    }
    return render(request, "chores.html", context)


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
