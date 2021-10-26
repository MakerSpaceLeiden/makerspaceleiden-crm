from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Mainssensor
from .decorators import superuser_or_mainsadmin_required
from members.models import Tag, User, clean_tag_string
from acl.models import Entitlement, PermitType

from makerspaceleiden.decorators import superuser_or_bearer_required

from .forms import NewMainssensorForm, MainssensorForm

import logging
import datetime
import re
from django.utils import timezone

logger = logging.getLogger(__name__)


@csrf_exempt
# Not required - simple innocent read at this time.
# @superuser_or_bearer_required
def resolve(request, tag=None):
    if request.POST:
        return HttpResponse("XS denied\n", status=403, content_type="text/plain")

    if tag:
        try:
            item = Mainssensor.objects.get(tag=tag)
            return render(
                request, "single-sensor.txt", {"item": item}, content_type="text/plain"
            )
        except:
            return HttpResponse(
                "Unknown sensor id\n", status=404, content_type="text/plain"
            )

    items = Mainssensor.objects.all().order_by("tag")
    return render(request, "sensors.txt", {"items": items}, content_type="text/plain")


@login_required
def index(request):
    items = Mainssensor.objects.all().order_by("tag")

    return render(
        request,
        "sensors.html",
        {
            "has_permission": request.user.is_authenticated,
            "items": items,
            "user": request.user,
            "canedit": request.user.is_privileged
            or request.user.groups.filter(name=settings.SENSOR_USER_GROUP).exists(),
        },
    )


@login_required
@superuser_or_mainsadmin_required
def create(request):
    if request.method == "POST":
        form = NewMainssensorForm(request.POST or None)
        if form.is_valid():
            try:
                form.changeReason = (
                    "Sensor Created through the self-service interface by {0}".format(
                        request.user
                    )
                )
                form.save()

                return redirect("mainsindex")
            except Exception as e:
                logger.error(
                    "Unexpected error during create of new mainssensor : {0}".format(e)
                )
    else:
        form = NewMainssensorForm()

    print(form)

    context = {
        "label": "New sensor",
        "action": "Create",
        "title": "Create a Mainssensor",
        "form": form,
        "back": "mainsindex",
        "user": request.user,
    }
    return render(request, "crud.html", context)


@login_required
@superuser_or_mainsadmin_required
def modify(request, pk):
    try:
        mainssensor = Mainssensor.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return HttpResponse("Sensor not found", status=404, content_type="text/plain")

    if request.method == "POST":
        form = MainssensorForm(
            request.POST or None, request.FILES, instance=mainssensor
        )
        if form.is_valid():
            logger.error("saving")
            try:
                mainssensor.changeReason = (
                    "Updated through the self-service interface by {0}".format(
                        request.user
                    )
                )
                mainssensor.save()
                for f in form.fields:
                    form.fields[f].widget.attrs["readonly"] = True
                return redirect("mainsindex")

            except Exception as e:
                logger.error(
                    "Unexpected error during save of mainssensor: {0}".format(e)
                )
    else:
        form = MainssensorForm(request.POST or None, instance=mainssensor)

    context = {
        "label": "Update mainssensor location and details",
        "action": "Update",
        "title": "Update mainssensor details",
        "user": request.user,
        "form": form,
        "back": "mainsindex",
    }

    return render(request, "crud.html", context)


@login_required
@superuser_or_mainsadmin_required
def delete(request, pk):
    try:
        mainssensor = Mainssensor.objects.get(pk=pk)
    except Mainssensor.DoesNotExist:
        return HttpResponse("Sensor not found", status=404, content_type="text/plain")

    try:
        mainssensor.delete()
    except Exception as e:
        logger.error("Unexpected error during delete of mainssensor: {0}".format(e))
        return HttpResponse("Sensor fail", status=400, content_type="text/plain")

    return redirect("mainsindex")
