from django.contrib.sites.shortcuts import get_current_site
from django.template import loader
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q

import datetime

from .models import Storage
from members.models import User
from .admin import StorageAdmin
from .forms import StorageForm,ConfirmForm

import logging
logger = logging.getLogger(__name__)

@login_required
def index(request,user_pk):
    historic = []
    pending = []
    rejected = []
    storage = []
    owner = 'everyone'

    sc = Storage.objects.all()
    if user_pk:
       owner = User.objects.get(pk=user_pk)
       sc = sc.filter(owner_id = user_pk)
    for i in sc:
       if i.expired() or i.state in ('EX', 'D'):
           historic.append(i)
       elif i.state in ('NO'):
           rejected.append(i)
       elif i.state in ('R', '1st'):
           pending.append(i)
       else:
           storage.append(i)

    canedit = {}
    for i in storage:
       if i.owner == request.user and i.editable() == True:
          canedit[ i ] = True
    for i in pending:
       if i.owner == request.user and i.editable() == True:
          canedit[ i ] = True

    context = {
        'title': 'Storage',
        'user' : request.user,
        'has_permission': request.user.is_authenticated,
        'overview' : {
            'Approved': storage,
            'Awaiting approval' : pending,
            'Rejected' : rejected,
            'Historic' : historic,
        },
        'limit': user_pk,
        'owner': owner,
        'canedit' : canedit,
    }
    return render(request, 'storage/index.html', context)

@login_required
@csrf_protect
def create(request):
    form = StorageForm(request.POST or None, initial = { 'owner': request.user.id })
    form.fields['duration'].help_text= "days. Short requests (month or less) are automatically approved."
    logger.error("WE have:" +str(request.POST))
    if form.is_valid():
       try:
           logger.error("Ok!")
           s = form.save(commit=False)
           s.changeReason = 'Created through the self-service interface by {0}'.format(request.user)
           s.save()
           s.apply_rules()
           return redirect('storage')
       except Exception as e:
           logger.error("Unexpected error during create of new box : {0}".format(e))
    else:
       logger.error("nope: " + str(form.errors))
       logger.error("nope: " + str(form.non_field_errors))

    context = {
        'label': 'Request a storage excemption',
        'action': 'Create',
        'title': 'Create Storage',
        'is_logged_in': request.user.is_authenticated,
        'user' : request.user,
        'owner' : request.user,
        'form':  form,
    }
    return render(request, 'storage/crud.html', context)

@login_required
@csrf_protect
def modify(request,pk):
    try:
         box = Storage.objects.get(pk=pk)
    except Storage.DoesNotExist:
         return HttpResponse("Eh - what box ??",status=404,content_type="text/plain")

    if not box.editable():
         return HttpResponse("Eh - no can do ??",status=403,content_type="text/plain")

    form = StorageForm(request.POST or None, instance = box)

    if form.is_valid():
       logger.error("saving")
       try:
           box = form.save(commit=False)
           box.changeReason = 'Updated through the self-service interface by {0}'.format(request.user)
           box.save()
           box.apply_rules()
           return redirect('storage')

       except Exception as e:
         logger.error("Unexpected error during save of box: {0}".format(e))
    else:
       logger.error("nope")

    context = {
        'label': 'Update box location and details',
        'action': 'Update',
        'title': 'Update box details',
        'is_logged_in': request.user.is_authenticated,
        'user' : request.user,
        'owner' : box.owner,
        'form':  form,
        'box': box,
    }

    return render(request, 'storage/crud.html', context)

@login_required
@csrf_protect
def delete(request,pk):
    try:
         box = Storage.objects.get(pk=pk)
    except Storage.DoesNotExist:
         return HttpResponse("Eh - what box ??",status=404,content_type="text/plain")

    if box.owner != request.user:
         return HttpResponse("Eh - not your box ?!",status=403,content_type="text/plain")

    if not request.POST:
         form = ConfirmForm(initial = {'pk':pk})
         context = {
            'title': 'Confirm delete',
            'label': 'Confirm puring storage request',
            'action': 'Delete',
            'is_logged_in': request.user.is_authenticated,
            'user' : request.user,
            'owner' : box.owner,
            'form':  form,
            'box': box,
            'delete': True,
         }
         return render(request, 'storage/crud.html', context)

    try:
       box.changeReason = 'Set to done via the self-service interface by {0}'.format(request.user)
       box.state = 'D'
       box.save()
    except Exception as e:
         logger.error("Unexpected error during delete of box: {0}".format(e))
         return HttpResponse("Box fail",status=400,content_type="text/plain")

    return redirect('storage')
