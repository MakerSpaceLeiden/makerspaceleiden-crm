from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_safe

from .forms import AgendaForm
from .models import Agenda


@login_required
def AgendaDeleteView(request, pk):
    agenda = get_object_or_404(Agenda, pk=pk)

    if request.method == "POST":
        agenda.delete()
        messages.success(request, "Message of the day deleted successfully.")
        return redirect("agenda")

    context = {
        "object": agenda,
        "title": "Confirm deletion",
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "agenda/agenda_confirm_delete.html", context)


@login_required
def AgendaUpdateView(request, pk):
    agenda = get_object_or_404(Agenda, pk=pk)

    if request.method == "POST":
        form = AgendaForm(request.POST, instance=agenda)
        if form.is_valid():
            form.save()
            messages.success(request, "The item is updated successfully.")
            return redirect("agenda_update", pk=pk)
    else:
        form = AgendaForm(instance=agenda)

    context = {
        "form": form,
        "title": "Edit agenda item",
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "agenda/agenda_crud.html", context)


@login_required
def AgendaCreateView(request):
    if request.method == "POST":
        form = AgendaForm(request.POST)
        if form.is_valid():
            user = request.user
            form.instance.user = user
            new_item = form.save()
            messages.success(request, "The agenda item is saved successfully.")

            # Redirect to agenda page with pk of the new item
            return redirect(reverse("agenda_detail", kwargs={"pk": new_item.pk}))
    else:
        form = AgendaForm()

    context = {
        "form": form,
        "title": "Create new agenda item",
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "agenda/agenda_crud.html", context)


@require_safe
@login_required
def AgendaItemsView(request, pk=None):
    show_history = request.GET.get(
        "show_history", "off"
    )  # Get the state of the show_history parameter
    now = timezone.now()

    if show_history == "off":
        agenda_list = Agenda.objects.filter(Q(enddate__gte=date.today())).order_by(
            "enddate", "endtime", "startdate", "starttime"
        )  # Filter out items with endtime and date after now
    else:
        agenda_list = Agenda.objects.all().order_by(
            "enddate", "endtime", "startdate", "starttime"
        )

    selected_item = None

    if agenda_list.exists():
        if pk:
            selected_item = get_object_or_404(Agenda, pk=pk)
        else:
            selected_item = (
                Agenda.objects.filter(
                    Q(enddate=date.today(), endtime__gte=now)
                    | Q(enddate__gt=date.today())
                )
                .order_by("enddate", "endtime", "startdate", "starttime")
                .first()
            )

    is_updated = False
    creation_date = "Time Unknown"
    created_by = "Unknown"
    update_date = "Time Unknown"
    updated_by = "Unknown"

    if selected_item:
        history = selected_item.history.all()
        if history.exists():
            if history.first().history_date != history.last().history_date:
                is_updated = True

            creation_date = history.first().history_date
            created_by = history.first().history_user
            update_date = history.last().history_date
            updated_by = history.last().history_user

    context = {
        "object_list": agenda_list,
        "selected_item": selected_item,
        "title": "Agenda",
        "has_permission": request.user.is_authenticated,
        "show_history": show_history,
    }

    if selected_item:
        context.update(
            {
                "creation_date": creation_date,
                "created_by": created_by,
            }
        )

    if is_updated:
        context.update(
            {
                "is_updated": is_updated,
                "update_date": update_date,
                "updated_by": updated_by,
            }
        )

    return render(request, "agenda/agenda.html", context)
