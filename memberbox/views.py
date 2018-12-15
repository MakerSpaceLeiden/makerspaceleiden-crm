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
from django.contrib.admin.sites import AdminSite
from django.utils import six

import logging
import re

from members.models import User
from .models import Memberbox
from .admin import MemberboxAdmin
from .forms import MemberboxForm, NewMemberboxForm

logger = logging.getLogger(__name__)

@login_required
def index(request):
    tmp = {}
    sizes_c = {}
    sizes_r = {}
    floating = []
    yours = Memberbox.objects.filter(owner = request.user).order_by('location')
    for box in Memberbox.objects.order_by('location'):
      m=re.search(r'^([LR]{1})(\d{1})(\d{1})$', box.location)
      if m:
        k = m.group(1)
        r = int(m.group(2))
        c = int(m.group(3))

        if not k in tmp:
          tmp[ k ] = {}
          sizes_r[k] = r
          sizes_c[k] = c

        if r >  sizes_r[k]:
           sizes_r[k] = r
        if c >  sizes_c[k]:
           sizes_c[k] = c
        
        if not r in tmp[k]:
           tmp[k][r] ={} 

        tmp[k][r][c] = box
      else:
        floating.append(box)

    labels = { 
             'L' : 'Left cabinet (near door)' , 
             'R' : 'Right cabinet (near WC)' , 
    }
    boxes = {}
    for k,contents in tmp.items():
       contents = []
       for r in range(1,sizes_r[k]+1):
         row = []
         for c in range(1,sizes_c[k]+1):
            try:
              row.append(tmp[k][r][c])
            except Exception as e:
              row.append('')

         contents.append(row)
       if k in labels:
         k = labels[k]
       boxes[k] = contents

    context = {
        'title': 'Storage',
        'user' : request.user,
        'has_permission': request.user.is_authenticated,
        'boxes': boxes,
        'floating': floating,
        'yours': yours,
    }

    return render(request, 'memberbox/index.html', context)

@login_required
def create(request):

    form = NewMemberboxForm(request.POST or None, initial = { 'owner': request.user.id })
    if form.is_valid():
       logger.error("saving")
       try:
           form.changeReason = 'Created through the self-service interface by {0}'.format(request.user)
           form.save()
           for f in form.fields:
             form.fields[f].widget.attrs['readonly'] = True
           return redirect('boxes')
       except Exception as e:
         logger.error("Unexpected error during create of new box : {0}".format(e))
    else:
       logger.error("nope")

    context = {
        'label': 'Describe a new box',
        'action': 'Create',
        'title': 'Create Memberbox',
        'is_logged_in': request.user.is_authenticated,
        'user' : request.user,
        'owner' : request.user,
        'form':  form,
    }
    return render(request, 'memberbox/crud.html', context)

@login_required
def modify(request,pk):
    try:
         box = Memberbox.objects.get(pk=pk)
    except Memberbox.DoesNotExist:
         return HttpResponse("Eh - what box ??",status=404,content_type="text/plain")

    form = MemberboxForm(request.POST or None, instance = box)
    if form.is_valid():
       logger.error("saving")
       try:
           box.changeReason = 'Updated through the self-service interface by {0}'.format(request.user)
           box.save()
           for f in form.fields:
             form.fields[f].widget.attrs['readonly'] = True
           return redirect('boxes')

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
    }

    return render(request, 'memberbox/crud.html', context)

@login_required
def delete(request,pk):
    try:
         box = Memberbox.objects.get(pk=pk)
    except Memberbox.DoesNotExist:
         return HttpResponse("Eh - what box ??",status=404,content_type="text/plain")


    if box.owner != request.user:
         return HttpResponse("Eh - not your box ?!",status=403,content_type="text/plain")

    try:
       box.delete()
    except Exception as e:
         logger.error("Unexpected error during delete of box: {0}".format(e))
         return HttpResponse("Box fail",status=400,content_type="text/plain")

    return redirect('boxes')
