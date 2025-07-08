import logging

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from simple_history.admin import SimpleHistoryAdmin

from members.models import User

from .forms import ConfirmForm, StorageForm
from .models import Storage

logger = logging.getLogger(__name__)


def sendStorageEmail(storedObject, user, isCreated, to, template):
    subject = "[makerbot] Storage request for %s" % storedObject.what
    if storedObject.state == "AG":
        subject += "(Auto approved, shorter than 30 days)"

    context = {
        "rq": storedObject,
        "user": user,
        "base": settings.BASE,
    }
    count = (
        Storage.objects.all()
        .filter(owner=storedObject.owner)
        .filter(Q(state="OK") | Q(state="AG"))
        .count()
    )
    if count > settings.STORAGE_HIGHLIGHT_LIMIT:
        context["count"] = count
    if isCreated:
        context["created"] = True

    message = render_to_string(template, context)
    EmailMessage(
        subject, message, to=[to], from_email=settings.DEFAULT_FROM_EMAIL
    ).send()


@login_required
def index(request, user_pk):
    historic = []
    pending = []
    rejected = []
    storage = []
    owner = "everyone"

    sc = Storage.objects.all().order_by("requested", "id").reverse()
    if user_pk:
        try:
            owner = User.objects.get(pk=user_pk)
        except ObjectDoesNotExist:
            return HttpResponse("User not found", status=404, content_type="text/plain")
        sc = sc.filter(owner_id=user_pk)
    for i in sc:
        if i.expired() or i.state in ("EX", "D"):
            historic.append(i)
        elif i.state in ("NO"):
            rejected.append(i)
        elif i.state in ("R", "1st"):
            pending.append(i)
        else:
            storage.append(i)

    canedit = {}
    for i in storage:
        if i.owner == request.user and i.editable() is True:
            canedit[i] = True
    for i in pending:
        if i.owner == request.user and i.editable() is True:
            canedit[i] = True

    context = {
        "title": "Storage",
        "user": request.user,
        "has_permission": request.user.is_authenticated,
        "overview": {
            "Approved": storage,
            "Awaiting approval": pending,
            "Rejected": rejected,
            "Historic": historic,
        },
        "limit": user_pk,
        "owner": owner,
        "canedit": canedit,
    }
    return render(request, "storage/index.html", context)


@login_required
def showstorage(request, pk):
    # not implemented yet.
    return redirect("storage")


@login_required
def create(request):
    if request.method == "POST":
        form = StorageForm(
            request.POST or None, request.FILES, initial={"owner": request.user}
        )
        if form.is_valid():
            try:
                s = form.save(commit=False)
                s.changeReason = (
                    "Created through the self-service interface by {0}".format(
                        request.user
                    )
                )
                s.save()
                s.apply_rules(request.user)

                sendStorageEmail(
                    s,
                    request.user,
                    True,
                    settings.MAILINGLIST,
                    "storage/email_change_general.txt",
                )
                if request.user != s.owner:
                    sendStorageEmail(
                        s,
                        request.user,
                        True,
                        s.owner.email,
                        "storage/email_change_owner.txt",
                    )

                return redirect("storage")
            except Exception as e:
                logger.error(
                    "Unexpected error during create of new storage : {0}".format(e)
                )
    else:
        form = StorageForm(initial={"owner": request.user})

    context = {
        "label": "Request a storage excemption",
        "action": "Create",
        "title": "Create Storage",
        "is_logged_in": request.user.is_authenticated,
        "user": request.user,
        "owner": request.user,
        "form": form,
        "has_permission": request.user.is_authenticated,
        "back": "storage",
    }
    return render(request, "storage/crud.html", context)


@login_required
def modify(request, pk):
    try:
        storage = Storage.objects.get(pk=pk)
    except Storage.DoesNotExist:
        return HttpResponse("Storage not found", status=404, content_type="text/plain")

    if not storage.editable() and not storage.location_updatable():
        return HttpResponse("Eh - no can do ??", status=403, content_type="text/plain")

    if request.method == "POST":
        form = StorageForm(request.POST or None, request.FILES, instance=storage)
        if form.is_valid():
            try:
                storage = form.save(commit=False)
                storage.changeReason = (
                    "Updated through the self-service interface by {0}".format(
                        request.user
                    )
                )
                storage.save()
                storage.apply_rules(request.user)

                sendStorageEmail(
                    storage,
                    request.user,
                    False,
                    settings.MAILINGLIST,
                    "storage/email_change_general.txt",
                )
                if request.user != storage.owner:
                    sendStorageEmail(
                        storage,
                        request.user,
                        False,
                        storage.owner.email,
                        "storage/email_change_owner.txt",
                    )

                return redirect("storage")

            except Exception as e:
                logger.error("Unexpected error during save of storage: {0}".format(e))
    else:
        form = StorageForm(instance=storage)
    context = {
        "label": "Update storage location and details",
        "action": "Update",
        "title": "Update storage details",
        "is_logged_in": request.user.is_authenticated,
        "user": request.user,
        "owner": storage.owner,
        "form": form,
        "storage": storage,
        "has_permission": request.user.is_authenticated,
        "back": "storage",
    }

    return render(request, "storage/crud.html", context)


@login_required
def delete(request, pk):
    try:
        storage = Storage.objects.get(pk=pk)
    except Storage.DoesNotExist:
        return HttpResponse("Storage not found", status=404, content_type="text/plain")

    form = ConfirmForm(request.POST or None, initial={"pk": pk})
    if not request.POST:
        context = {
            "title": "Confirm delete",
            "label": "Confirm puring storage request",
            "action": "Delete",
            "is_logged_in": request.user.is_authenticated,
            "user": request.user,
            "owner": storage.owner,
            "form": form,
            "storage": storage,
            "delete": True,
            "has_permission": request.user.is_authenticated,
            "back": "storage",
        }
        return render(request, "storage/crud.html", context)

    if not form.is_valid():
        return HttpResponse("Eh - confused ?!", status=403, content_type="text/plain")

    if storage.owner != request.user and form.cleaned_data["pk"] != pk:
        return HttpResponse(
            "Eh - not your storage ?!", status=403, content_type="text/plain"
        )

    try:
        storage.changeReason = (
            "Set to done via the self-service interface by {0}".format(request.user)
        )
        storage.state = "D"
        storage.save()
    except Exception as e:
        logger.error("Unexpected error during delete of storage: {0}".format(e))
        return HttpResponse("Box fail", status=400, content_type="text/plain")

    return redirect("storage")


class MySimpleHistoryAdmin(SimpleHistoryAdmin):
    object_history_template = "storage/object_history.html"

    # Bit risky - routes in to bypass for naughtyness in below showhistory.
    def has_change_permission(self, request, obj):
        return True


@login_required
def showhistory(request, pk, rev=None):
    try:
        storage = Storage.objects.get(pk=pk)
    except Storage.DoesNotExist:
        return HttpResponse(
            "Storage not found", pk, status=404, content_type="text/plain"
        )
    context = {
        "title": "View history",
        #       'opts': { 'admin_url': { 'simple_history': 'xxx' } },
    }
    if rev:
        revInfo = storage.history.get(pk=rev)
        historic = revInfo.instance
        form = StorageForm(instance=historic)
        context = {
            "title": "Historic record",
            "label": revInfo,
            "action": None,
            "is_logged_in": request.user.is_authenticated,
            "user": request.user,
            "owner": storage.owner,
            "form": form,
            "storage": historic,
            "history": True,
            "has_permission": request.user.is_authenticated,
            "back": "storage",
        }
        return render(request, "storage/crud.html", context)

    historyAdmin = MySimpleHistoryAdmin(Storage, AdminSite())
    return historyAdmin.history_view(request, str(pk), context)


def nope(request):
    return HttpResponse(
        "No storage functionality", status=404, content_type="text/plain"
    )
