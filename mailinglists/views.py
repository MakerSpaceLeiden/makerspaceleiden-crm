from django.shortcuts import render,redirect
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
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from makerspaceleiden.decorators import superuser_or_bearer_required

from .forms import SubscriptionForm

import json

from members.models import User

from acl.models import Machine,Entitlement,PermitType

from .models import Mailinglist, Subscription

from storage.models import Storage
from memberbox.models import Memberbox

import logging
logger = logging.getLogger(__name__)

@login_required
def mailinglists_edit(request):
    lists = Mailinglist.objects.all()
    subs = Subscription.objects.all().filter(member = request.user)

    # In theory we could assume a perfectly synced DB; but we'll for now
    # allow discrepancies - and simply add any missing subscriptions if
    # needed on the next save of this form.
    #
    id2list = {}
    id2sub = {}
    for l in lists:
        id2list[str(l.id)] = l
        id2sub[str(l.id)] = None

    for s in subs:
        id2sub[str(s.mailinglist.id)] = s

    if request.method == "POST":
        # TODO: We skip the disabled on active for manadatory lists. 
        forms = [ SubscriptionForm(request.POST, prefix=str(l.id), instance = id2sub[ str(l.id) ]) for l in lists ]
        if all([form.is_valid() for form in forms]):
            for form in forms:
                nw= form.save(commit=False)
                nw.member = request.user
                nw.mailinglist = id2list[ form.prefix ]
                nw.save()
            return redirect('mailinglists_edit')

    forms = []
    for l in lists:
        # As per above 'not perfect' note -- See if we already have this subscription or not; and then use that
        # to populate our values; otherwise pick up a brand new one.
        #
        s = [ s for s in subs if s.mailinglist == l ]
        if s:
           s = s[0]
        if s:
           form = SubscriptionForm(prefix=str(l.id), instance = s)
        else:
           form = SubscriptionForm(prefix=str(l.id)) 
        if l.mandatory:
           form.fields['active'].value = True
           form.fields['active'].disabled = True
           form.fields['active'].help_text = 'This list is mandatory for all members. It cannot be disabled. Contact the trustees for exceptions.'

        forms.append((l, form))

    return render(request,'multi_crud.html', {
          'title': 'Edit your mailing lists subscriptions',
          'forms': forms,
          'action': 'Submit',
          'back': 'mailinglists_edit',
    })


