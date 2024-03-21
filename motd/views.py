import logging
import requests

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

import models

logger = logging.getLogger(__name__)

@login_required
def motd(request):
    context = {}
    context["msgs"] = MotD.objects.order_by("date")

    return render(request, "motd/motd.html", context)
