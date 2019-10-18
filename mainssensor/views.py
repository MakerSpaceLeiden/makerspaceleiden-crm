from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Mainssensor
from members.models import Tag,User,clean_tag_string
from acl.models import Entitlement,PermitType

from makerspaceleiden.decorators import superuser_or_bearer_required

import logging
import datetime
import re
from django.utils import timezone

logger = logging.getLogger(__name__)

@csrf_exempt
# Not required - simple innocent read at this time.
# @superuser_or_bearer_required 
def resolve(request, tag = None):
  if request.POST:
         return HttpResponse("XS denied\n",status=403,content_type="text/plain")

  if tag:
      try:
           item = Mainssensor.objects.get(tag = tag);
           return render(request, 'single-sensor.txt', { 'item': item }, content_type="text/plain")
      except:
           return HttpResponse("Unknown sensor id\n",status=404,content_type="text/plain")

  items = Mainssensor.objects.all().order_by('tag')
  return render(request, 'sensors.txt', { 'items': items }, content_type="text/plain")

@login_required
def index(request):
  items =  Mainssensor.objects.all().order_by('tag');

  return render(request, 'sensors.html', { 
               'has_permission': request.user.is_authenticated,
               'items': items,
		'user': request.user,
         })
