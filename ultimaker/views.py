import logging

import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def index(request):
    return render(request, "ultimaker/index.html", {})


def snapshot(request):
    img = requests.get("http://127.0.0.1:9998/?action=snapshot").content
    return HttpResponse(img, content_type="image/jpeg")
