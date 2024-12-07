import datetime
import logging
import os
import re
import uuid
import zipfile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, IntegerField, Q, Value, When
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from ufo.utils import emailUfoInfo

from .forms import NewUfoForm, UfoForm, UfoZipUploadForm
from .models import Ufo

logger = logging.getLogger(__name__)


# Note - we do this here; rather than in the model its save() - as this
# lets admins change things through the database interface silently.
# Which can help when sheparding the community.
#
def alertOwnersToChange(items, userThatMadeTheChange=None, toinform=[]):
    _ = {
        "user": userThatMadeTheChange,
        "base": settings.BASE,
    }
    if userThatMadeTheChange:
        toinform.append(userThatMadeTheChange.email)

    if settings.ALSO_INFORM_EMAIL_ADDRESSES:
        toinform.extend(settings.ALSO_INFORM_EMAIL_ADDRESSES)

    return emailUfoInfo(items, "email_notification", toinform=[], context={})


def ufo_redirect(pk=None):
    url = reverse("ufo")
    if pk:
        url = "{}#{}".format(url, pk)
    return redirect(url)


def index(request, days=30):
    lst = Ufo.objects.all()
    if days > 0:
        tooOld = datetime.date.today() - datetime.timedelta(days=days)
        lst = lst.filter(Q(lastChange__gte=tooOld) | Q(state="UNK"))

    lst = lst.annotate(
        priority=Case(
            When(state="UNK", then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by("priority", "created_at")

    context = {
        "title": "Unclaimed Floating Objects",
        "lst": lst,
        "days": days,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "ufo/index.html", context)


@login_required
def create(request):
    form = NewUfoForm(request.POST or None, request.FILES, initial={"state": "UNK"})
    if form.is_valid():
        try:
            item = form.save(commit=False)

            item.state = "UNK"
            if not item.description:
                item.description = "Added by {}".format(request.user)

            item.changeReason = "Created by {} through the self-service portal.".format(
                request.user
            )
            item.save()

            # Try to alert owners, but don't give an error in the frontend if it doesn't work
            try:
                alertOwnersToChange(item, request.user, [item.owner.email])
            except Exception as e:
                logger.error("Failed to alert owners: {}".format(e))

            # Redirect after successful save
            return ufo_redirect(item.id)

        except Exception as e:
            logger.error(
                "Unexpected error during initial save of new ufo: {}".format(e)
            )

        return HttpResponse(
            "Something went wrong ??", status=500, content_type="text/plain"
        )

    context = {
        "title": "Add an Unclaimed Floating Object",
        "form": form,
        "action": "Add",
        "has_permission": request.user.is_authenticated,
        "back": "ufo",
    }
    return render(request, "crud.html", context)


def show(request, pk):
    try:
        item = Ufo.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return HttpResponse("UFO not found", status=404, content_type="text/plain")

    context = {
        "title": "Unclaimed Floating Objects",
        "item": item,
        "has_permission": request.user.is_authenticated,
    }
    return render(request, "ufo/view.html", context)


@login_required
def modify(request, pk):
    try:
        oitem = Ufo.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return HttpResponse("UFO not found", status=404, content_type="text/plain")

    toinform = []
    if oitem.owner:
        toinform.append(oitem.owner.email)

    context = {
        "title": "Update an Unclaimed Floating Object",
        "action": "Update",
        "item": oitem,
        "has_permission": request.user.is_authenticated,
    }
    if request.POST:
        form = UfoForm(request.POST or None, request.FILES, instance=oitem)
        if form.is_valid() and request.POST:
            try:
                item = form.save(commit=False)
                item.changeReason = "Changed by {} via self service portal".format(
                    request.user
                )
                item.save()
            except Exception as e:
                logger.error("Unexpected error during update of ufo: {}".format(e))

            if item.owner:
                toinform.append(item.owner.email)

            alertOwnersToChange([item], request.user, toinform)

            context["item"] = item

            return ufo_redirect(pk)

    form = UfoForm(instance=oitem)
    context["form"] = form
    context["back"] = "ufo"

    return render(request, "crud.html", context)


@login_required
def mine(request, pk):
    try:
        item = Ufo.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return HttpResponse("UFO not found", status=404, content_type="text/plain")

    item.changeReason = "claimed as 'mine' by {} via self service portal".format(
        request.user
    )
    if item.owner != request.user:
        dst = []
        if item.owner and item.owner.email:
            dst.append(item.owner.email)
        # Try to alert any owners, but$ don't give an error in the frontend if it doesn't work
        try:
            alertOwnersToChange([item], request.user, dst)
        except Exception as e:
            logger.error("Failed to alert owners: {}".format(e))

    item.state = "OK"
    item.claimed_by = request.user
    item.claimed_at = datetime.datetime.now()

    item.save()

    return ufo_redirect(pk)


@login_required
# Limit this to admins ?
def delete(request, pk):
    try:
        item = Ufo.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return HttpResponse("UFO not found", status=404, content_type="text/plain")

    form = UfoForm(request.POST or None, instance=item)
    for f in form.fields:
        form.fields[f].disabled = True

    if not request.POST:
        context = {
            "title": "Confirm delete of this UFO",
            "label": "Confirm delete of this UFO",
            "action": "Delete",
            "is_logged_in": request.user.is_authenticated,
            "user": request.user,
            "form": form,
            "item": item,
            "delete": True,
            "back": "ufo",
        }
        return render(request, "crud.html", context)

    if not form.is_valid():
        return HttpResponse("Eh - confused ?!", status=403, content_type="text/plain")

    try:
        item.changeReason = "Deleted via the self-service interface by {0}".format(
            request.user
        )
        item.save()
        item.delete()
    except Exception as e:
        logger.error("Unexpected error during delete of item: {0}".format(e))
        return HttpResponse("Box fail", status=400, content_type="text/plain")

    return ufo_redirect()


@login_required
def upload_zip(request):
    form = UfoZipUploadForm(request.POST or None, request.FILES)
    if request.method == "POST":
        if form.is_valid() and "zipfile" in request.FILES:
            if request.FILES["zipfile"].size > settings.MAX_ZIPFILE:
                return HttpResponse(
                    "Upload too large", status=500, content_type="text/plain"
                )

            tmpZip = settings.MEDIA_ROOT + "/ufozip-" + str(uuid.uuid4())
            with open(tmpZip, "wb+") as dst:
                for c in request.FILES["zipfile"].chunks():
                    dst.write(c)

            skipped = []
            lst = []
            with zipfile.ZipFile(tmpZip, "r") as z:
                for zi in z.infolist():
                    f = zi.filename
                    if zi.is_dir():
                        skipped.append("{0}: skipped, directory".format(f))
                        continue
                    if re.match("\..*", f):
                        skipped.append("{0}: skipped, hidden file".format(f))
                        continue
                    if re.match(".*/\.", f):
                        skipped.append("{0}: skipped, hidden file".format(f))
                        continue
                    if zi.file_size < settings.MIN_IMAGE_SIZE:
                        skipped.append("{0}: skipped, too small".format(f))
                        continue
                    if zi.file_size > settings.MAX_IMAGE_SIZE:
                        skipped.append("{0}: skipped, too large".format(f))
                        continue

                    extension = "raw"
                    if re.match(".*\.(jpg|jpeg)$", f, re.IGNORECASE):
                        extension = "jpg"
                    elif re.match(".*\.(png)$", f, re.IGNORECASE):
                        extension = "png"
                    else:
                        skipped.append(
                            "{0}: skipped, does not have an image extension such as .jp(e)g or .png.".format(
                                f
                            )
                        )
                        continue

                    ufo = Ufo(description="Auto upload", state="UNK")

                    try:
                        with z.open(f) as fh:
                            fp = str(uuid.uuid4()) + "." + extension
                            ufo.image.save(fp, fh)
                    except Exception as e:
                        logger.error("Error during zip extract: {}".format(e))
                        skipped.append(
                            "{0}: skipped, could not be extracted.".format(f)
                        )
                        continue

                    for f in ["description", "deadline", "dispose_by_date"]:
                        if form.cleaned_data[f]:
                            setattr(ufo, f, form.cleaned_data[f])

                    ufo.changeReason = "Part of a bulk upload by {}".format(
                        request.user
                    )
                    ufo.save()

                    lst.append(ufo)
            try:
                os.remove(tmpZip)
            except Exception as e:
                logger.error("Error during cleanup of {}: {}".format(tmpZip, e))

            if lst:
                alertOwnersToChange(lst, request.user, [request.user.email])

            return render(
                request,
                "ufo/upload.html",
                {
                    "has_permission": request.user.is_authenticated,
                    "action": "Done",
                    "lst": lst,
                    "skipped": skipped,
                },
            )

    return render(
        request,
        "ufo/upload.html",
        {
            "form": form,
            "action": "Upload",
            "has_permission": request.user.is_authenticated,
        },
    )
