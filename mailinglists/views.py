from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django import forms
from django.forms import ModelForm
from django.core.exceptions import ObjectDoesNotExist

from django.views.decorators.csrf import csrf_exempt
from makerspaceleiden.decorators import superuser_or_bearer_required

import json
from django.http import JsonResponse
from ipware import get_client_ip

from members.models import Tag,User, clean_tag_string
from members.forms import TagForm

from .models import Machine,Entitlement,PermitType

from storage.models import Storage
from memberbox.models import Memberbox

import logging
logger = logging.getLogger(__name__)

@login_required
def list_edit(request)
    try:
       tag = Tag.objects.get(pk=tag_id)
    except ObjectDoesNotExist as e:
       return HttpResponse("Tag not found",status=404,content_type="text/plain")

    context = {
        'title': 'Update a tag',
        'action': 'Update',
        'item': tag
        }
    if request.POST:
     form = TagForm(request.POST or None, request.FILES, instance = tag, canedittag = request.user.is_superuser)
     if form.is_valid() and request.POST:
        try:
            item = form.save(commit = False)
            item.changeReason = "Changed by {} via self service portal".format(request.user)
            item.save()
        except Exception as e:
            logger.error("Unexpected error during update of tag: {}".format(e))

        return redirect('overview', member_id=item.owner_id)

    form = TagForm(instance = tag, canedittag = request.user.is_superuser)
    context['form'] = form

    return render(request, 'acl/crud.html', context)

