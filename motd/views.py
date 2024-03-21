import logging
import requests
from django.core import serializers

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .models import Motd

logger = logging.getLogger(__name__)

@login_required
def motd(request):
    context = {}
    context["msgs"] = Motd.objects.order_by("date")

    return render(request, "motd/motd.html", context)

@login_required
def motd_as_json(request):
    # msgs = serializers.serialize("json", Motd.objects.order_by("date"))
    # return HttpResponse(msgs.encode("utf8"),content_type="application/json")

    context = {}
    context["msgs"] = Motd.objects.order_by("date")

    return render(request, "motd/motd.json", context)
