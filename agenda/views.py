from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_safe

from .forms import AgendaForm
from .models import Agenda


def get_next_occurrence_of_weekday(target_weekday, from_date=None):
    """
    Calculate the next occurrence of a specific weekday from a given date.

    Args:
        target_weekday (int): Day of week (0=Monday, 6=Sunday)
        from_date (date): Starting date, defaults to today

    Returns:
        date: The next occurrence of the target weekday
    """
    if from_date is None:
        from_date = date.today()

    # Calculate days until next occurrence
    days_ahead = target_weekday - from_date.weekday()

    # If the target day is today or has passed this week, get next week's occurrence
    if days_ahead <= 0:
        days_ahead += 7

    return from_date + timedelta(days=days_ahead)


def get_suggested_dates_for_copy(startdate, enddate):
    """
    Calculate suggested start and end dates when copying an agenda item.

    Args:
        original_agenda (Agenda): The agenda item being copied

    Returns:
        tuple: (suggested_startdate, suggested_enddate)
    """
    suggested_startdate = startdate
    suggested_enddate = enddate

    if startdate:
        # Get the weekday of the original start date (0=Monday, 6=Sunday)
        original_start_weekday = startdate.weekday()
        suggested_startdate = get_next_occurrence_of_weekday(original_start_weekday)

    if enddate:
        if startdate and enddate:
            # If both dates exist, maintain the same relative timing
            # Calculate the difference between original start and end dates
            date_difference = enddate - startdate
            suggested_enddate = suggested_startdate + date_difference
        else:
            # If only end date exists, suggest next occurrence of that weekday
            original_end_weekday = enddate.weekday()
            suggested_enddate = get_next_occurrence_of_weekday(original_end_weekday)

    return suggested_startdate, suggested_enddate


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
        copy_from_id = request.GET.get("copy_from")
        initial = None
        if copy_from_id:
            try:
                copy_from = Agenda.objects.get(pk=copy_from_id)

                # Get suggested dates using the helper method
                suggested_startdate, suggested_enddate = get_suggested_dates_for_copy(
                    copy_from.startdate, copy_from.enddate
                )

                initial = {
                    "startdate": suggested_startdate,
                    "starttime": copy_from.starttime,
                    "enddate": suggested_enddate,
                    "endtime": copy_from.endtime,
                    "item_title": copy_from.item_title,
                    "item_details": copy_from.item_details,
                }
            except Agenda.DoesNotExist:
                initial = None

        form = AgendaForm(initial=initial)

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

    if show_history == "off":
        agenda_list = Agenda.objects.upcoming()
    else:
        agenda_list = Agenda.objects.all().order_by("_startdatetime", "item_title")

    selected_item = None

    if agenda_list.exists():
        if pk:
            selected_item = get_object_or_404(Agenda, pk=pk)
        else:
            selected_item = agenda_list.first()

    is_updated = False
    creation_date = "Time Unknown"
    created_by = "Unknown"
    update_date = "Time Unknown"
    updated_by = "Unknown"

    if selected_item:
        history = selected_item.history.all()
        if history.exists():
            if history.earliest().history_date != history.latest().history_date:
                is_updated = True

            creation_date = history.earliest().history_date
            created_by = history.earliest().history_user
            update_date = history.latest().history_date
            updated_by = history.latest().history_user

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
