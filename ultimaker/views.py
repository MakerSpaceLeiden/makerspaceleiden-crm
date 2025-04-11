import logging

import requests
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


@login_required
def index(request):
    context = {
        "has_permission": request.user.is_authenticated,
        "title": "Live 3D printer camera",
    }
    return render(request, "ultimaker/index.html", context)


def snapshot(request):
    try:
        img = requests.get("http://192.168.6.12:8080/?action=snapshot", timeout=15).content
    except Exception:
        return HttpResponse(
            "Ultimaker not on or LAN at space down", content_type="text/plain"
        )
    return HttpResponse(img, content_type="image/jpeg")
