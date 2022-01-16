from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone

from makerspaceleiden.decorators import superuser_or_bearer_required

import logging
import datetime
import re
import requests

logger = logging.getLogger(__name__)

# @login_required
def index(request):
    return render(request, "ultimaker/index.html", {})


def snapshot(request):
    img = requests.get("http://127.0.0.1:9998/?action=snapshot").content
    return HttpResponse(img, content_type="image/jpeg")
