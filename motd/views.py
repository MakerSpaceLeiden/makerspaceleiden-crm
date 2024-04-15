from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_safe

from .forms import MotdForm
from .models import Motd


@login_required
def MotdDeleteView(request, pk):
    motd = get_object_or_404(Motd, pk=pk)

    if request.method == "POST":
        motd.delete()
        messages.success(request, "Message of the day deleted successfully.")
        return redirect("motd_messages")

    context = {
        "object": motd,
        "title": "Confirm deletion",
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "motd/motd_confirm_delete.html", context)


@login_required
def MotdUpdateView(request, pk):
    motd = get_object_or_404(Motd, pk=pk)

    if request.method == "POST":
        form = MotdForm(request.POST, instance=motd)
        if form.is_valid():
            form.save()
            messages.success(request, "The message is updated successfully.")
            return redirect("motd_update", pk=pk)
    else:
        form = MotdForm(instance=motd)

    context = {
        "form": form,
        "title": "Edit message of the day",
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "motd/motd_crud.html", context)


@login_required
def MotdCreateView(request):
    if request.method == "POST":
        form = MotdForm(request.POST)
        if form.is_valid():
            user = request.user
            form.instance.user = user
            new_motd = form.save()
            messages.success(request, "The message is saved successfully.")

            # Redirect to motd_messages page with pk of the new message
            return redirect(reverse("motd_messages_detail", kwargs={"pk": new_motd.pk}))
    else:
        form = MotdForm()

    context = {
        "form": form,
        "title": "Create new message of the day",
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "motd/motd_crud.html", context)


@login_required
def MotdView(request):
    motd_items = Motd.objects.all().order_by("-startdate")[:10]
    return render(request, "motd/motd.html", {"motd_items": motd_items})


@require_safe
@login_required
def MotdMessagesView(request, pk=None):
    motd_list = Motd.objects.order_by(
        "-startdate", "-starttime", "-enddate", "-endtime"
    )
    selected_message = None

    if motd_list.exists():
        if pk:
            selected_message = get_object_or_404(Motd, pk=pk)
        else:
            selected_message = Motd.objects.order_by("id").first()

    is_updated = False
    creation_date = "Time Unknown"
    created_by = "Unknown"
    update_date = "Time Unknown"
    updated_by = "Unknown"

    if selected_message:
        history = selected_message.history.all()
        if history.exists():
            if history.first().history_date != history.last().history_date:
                is_updated = True

            creation_date = history.first().history_date
            created_by = history.first().history_user
            update_date = history.last().history_date
            updated_by = history.last().history_user

    context = {
        "object_list": motd_list,
        "selected_message": selected_message,
        "title": "Message of the day",
        "has_permission": request.user.is_authenticated,
    }

    if selected_message:
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

    return render(request, "motd/motd_messages.html", context)
