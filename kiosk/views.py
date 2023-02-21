import os
import logging
import json

from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.template import loader
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from makerspaceleiden.decorators import user_or_kiosk_required

from django.conf import settings


from selfservice.aggregator_adapter import get_aggregator_adapter


@user_or_kiosk_required
def kiosk(request):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )
    context = aggregator_adapter.fetch_state_space()
    context["user"] = None

    return render(request, "kiosk.html", context)
