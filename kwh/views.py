from django.shortcuts import render,redirect
from django.template import loader
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy,reverse
from django import forms
from django.forms import ModelForm
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import FileResponse

from time import strptime
import datetime
import json,os, re

from django.views.decorators.csrf import csrf_exempt
from makerspaceleiden.decorators import superuser_or_bearer_required

from members.models import User
from acl.models import Machine,Entitlement,PermitType

import logging
logger = logging.getLogger(__name__)

# @login_required
def kwh_proxy(request, path):
    if path == '':
        path = 'index.html'
    path = '/'+path
    if re.compile(r'^[\w/]*/[-\w]+\.\w+$').match(path):
       return FileResponse(open('/var/www/mrtg/'+path, 'rb'))

    logger.error("Rejecting '/crm/kwh/{}'.".format(path))
    return HttpResponse("XS denied",status=403,content_type="text/plain")

