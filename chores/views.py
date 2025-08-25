import json
import logging
import time
from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import pluralize
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from agenda.models import Agenda, AgendaChoreStatusChange

from .constants import CHORES_GENERATE_EVENTS_FOR_DAYS
from .forms import ChoreForm
from .helpers import create_chore_agenda_item
from .models import Chore, ChoreVolunteer
from .schedule import EventsGenerationConfiguration, generate_schedule_for_event

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


def processChore(c):
    c.name = c.name.replace("_", " ").title
    return c


@login_required
def index(request):
    chores = map(
        processChore,
        Chore.objects.prefetch_related(
            Prefetch(
                "agenda_set",
                queryset=Agenda.objects.upcoming(),
                to_attr="upcoming_events",
            ),
            Prefetch(
                "agenda_set",
                queryset=Agenda.objects.previous(),
                to_attr="previous_events",
            ),
        ).order_by("name"),
    )

    context = {
        "chores": chores,
        "title": "Chores",
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


@login_required
def preview_schedule(request):
    configuration: EventsGenerationConfiguration = {
        "event_type": "recurrent",
        "starting_time": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "crontab": request.GET.get("crontab"),
        "take_one_every": int(request.GET.get("take_one_every")),
        "duration": "P1W",
    }
    schedule = generate_schedule_for_event(
        configuration, int(request.GET.get("number_of_days"))
    )

    return JsonResponse(
        {
            "schedule": schedule,
            "crontab": request.GET.get("crontab"),
        }
    )


class ChoreCreateView(
    LoginRequiredMixin, SuccessMessageMixin, PermissionRequiredMixin, CreateView
):
    model = Chore
    form_class = ChoreForm
    template_name = "chores/chore_crud.html"
    context_object_name = "chore"
    permission_required = "chores.add_chore"

    success_message = "Chore created successfully."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create new chore"
        return ctx


class ChoreUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView
):
    permission_required = "chores.change_chore"
    model = Chore
    form_class = ChoreForm
    template_name = "chores/chore_crud.html"
    context_object_name = "chore"

    success_message = "Chore updated successfully."

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Edit chore"
        return ctx


class ChoreDetailView(LoginRequiredMixin, DetailView):
    model = Chore
    template_name = "chores/chore_detail.html"
    context_object_name = "chore"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        events = []
        for agenda in Agenda.objects.filter(chore=self.object):
            recent_completed_status_change = (
                AgendaChoreStatusChange.objects.filter(
                    agenda=agenda,
                )
                .order_by("-created_at")
                .first()
            )
            if (
                recent_completed_status_change
                and recent_completed_status_change.status != "completed"
            ):
                recent_completed_status_change = None

            events.append(
                {
                    "agenda": agenda,
                    "recent_completed_status_change": recent_completed_status_change,
                }
            )
        ctx["title"] = "Chores"
        ctx["name"] = self.object.name.replace("_", " ").title
        ctx["events"] = events
        return ctx


class ChoreDeleteView(LoginRequiredMixin, DeleteView):
    model = Chore
    template_name = "chores/chore_confirm_delete.html"
    context_object_name = "chore"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Confirm deletion"
        return ctx

    def get_success_url(self):
        return reverse("chores")


def generate_events_for_chore(request, pk):
    chore = get_object_or_404(Chore, pk=pk)
    events_config = chore.configuration["events_generation"]
    if not events_config["event_type"] == "recurrent":
        return HttpResponse(
            "Unsupported event_type", status=400, content_type="text/plain"
        )

    schedule = generate_schedule_for_event(
        events_config, CHORES_GENERATE_EVENTS_FOR_DAYS
    )

    print(f"Schedule: {schedule}")

    event_generated_count = 0

    for next in schedule:
        if create_chore_agenda_item(chore, next, logger):
            event_generated_count += 1

    if event_generated_count == 0:
        messages.info(
            request,
            f"No events were generated for {chore.name} in next {CHORES_GENERATE_EVENTS_FOR_DAYS} days",
        )
    else:
        messages.success(
            request,
            f"{event_generated_count} event{pluralize(event_generated_count)} generated for {chore.name}",
        )

    return redirect(reverse("chore_detail", kwargs={"pk": chore.pk}))
