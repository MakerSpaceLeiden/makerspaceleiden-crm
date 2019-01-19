from django.contrib.sites.shortcuts import get_current_site
from django.contrib.admin.sites import AdminSite
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
from simple_history.admin import SimpleHistoryAdmin
from django.template.loader import render_to_string, get_template
from django.core.mail import EmailMessage
from django.conf import settings

import datetime

from .models import Storage
from members.models import User
from .admin import StorageAdmin
from .forms import StorageForm,ConfirmForm

import logging
logger = logging.getLogger(__name__)


def sendStorageEmail(storedObject, user, isCreated, to, template):
    subject = "[makerbot] Storage request for %s" % storedObject.what
    if storedObject.state == 'AG':
           subject += '(Auto approved, shorter than 30 days)'

    context = {
           'rq': storedObject,
           'user': user,
           'base': settings.BASE,
    }
    count = Storage.objects.all().filter(owner = storedObject.owner).filter(Q(state = 'OK')|Q(state = 'AG')).count()
    if count > settings.STORAGE_HIGHLIGHT_LIMIT:
     context['count'] = count
    if isCreated:
     context['created'] = True

    message = render_to_string(template, context)
    EmailMessage(subject, message, to=[to], from_email=settings.DEFAULT_FROM_EMAIL).send()


@login_required
def index(request,user_pk):
    historic = []
    pending = []
    rejected = []
    storage = []
    owner = 'everyone'

    sc = Storage.objects.all().order_by('requested','id').reverse()
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
def showstorage(request, pk):
    # not implemented yet.
    return redirect('storage')

@login_required
@csrf_protect
def create(request):
    if request.method == "POST":
     form = StorageForm(request.POST or None, request.FILES, initial = { 'owner': request.user })
     if form.is_valid():
       try:
           s = form.save(commit=False)
           s.changeReason = 'Created through the self-service interface by {0}'.format(request.user)
           s.save()
           s.apply_rules(request.user)

           sendStorageEmail(s, request.user, True, 
                   settings.MAILINGLIST, 'storage/email_change_general.txt')
           if request.user != s.owner:
                   sendStorageEmail(s, request.user, True, 
                      s.owner.email, 'storage/email_change_owner.txt')

           return redirect('storage')
       except Exception as e:
           logger.error("Unexpected error during create of new storage : {0}".format(e))
    else:
      form = StorageForm(initial = { 'owner': request.user })

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
         storage = Storage.objects.get(pk=pk)
    except Storage.DoesNotExist:
         return HttpResponse("Eh - modify what storage ??",status=404,content_type="text/plain")

    if not storage.editable() and not storage.location_updatable():
         return HttpResponse("Eh - no can do ??",status=403,content_type="text/plain")

    if request.method == "POST":
      form = StorageForm(request.POST or None, request.FILES, instance = storage)
      if form.is_valid():
       try:
           storage = form.save(commit=False)
           storage.changeReason = 'Updated through the self-service interface by {0}'.format(request.user)
           storage.save()
           storage.apply_rules(request.user)

           sendStorageEmail(storage, request.user, False, 
                   settings.MAILINGLIST, 'storage/email_change_general.txt')
           if request.user != storage.owner:
                   sendStorageEmail(storage, request.user, False, 
                      storage.owner.email, 'storage/email_change_owner.txt')

           return redirect('storage')

       except Exception as e:
         logger.error("Unexpected error during save of storage: {0}".format(e))
    else:
       form = StorageForm(instance = storage)
    context = {
        'label': 'Update storage location and details',
        'action': 'Update',
        'title': 'Update storage details',
        'is_logged_in': request.user.is_authenticated,
        'user' : request.user,
        'owner' : storage.owner,
        'form':  form,
        'storage': storage,
    }

    return render(request, 'storage/crud.html', context)

@login_required
@csrf_protect
def delete(request,pk):
    try:
         storage = Storage.objects.get(pk=pk)
    except Storage.DoesNotExist:
         return HttpResponse("Eh - delete what storage ??",status=404,content_type="text/plain")

    form = ConfirmForm(request.POST or None, initial = {'pk':pk})
    if not request.POST:
         context = {
            'title': 'Confirm delete',
            'label': 'Confirm puring storage request',
            'action': 'Delete',
            'is_logged_in': request.user.is_authenticated,
            'user' : request.user,
            'owner' : storage.owner,
            'form':  form,
            'storage': storage,
            'delete': True,
         }
         return render(request, 'storage/crud.html', context)

    if not form.is_valid():
         return HttpResponse("Eh - confused ?!",status=403,content_type="text/plain")

    if storage.owner != request.user and form.cleaned_data['pk'] != pk:
         return HttpResponse("Eh - not your storage ?!",status=403,content_type="text/plain")

    try:
       storage.changeReason = 'Set to done via the self-service interface by {0}'.format(request.user)
       storage.state = 'D'
       storage.save()
    except Exception as e:
         logger.error("Unexpected error during delete of storage: {0}".format(e))
         return HttpResponse("Box fail",status=400,content_type="text/plain")

    return redirect('storage')

class MySimpleHistoryAdmin(SimpleHistoryAdmin):
    object_history_template = "storage/object_history.html"
    # object_history_form_template = "storage/object_history_form.html"

    # Bit risky - routes in to bypass for naughtyness in below showhistory.
    def has_change_permission(self, request, obj):
       return True

@login_required
@csrf_protect
def showhistory(request,pk,rev=None):
    try:
         storage = Storage.objects.get(pk=pk)
    except Storage.DoesNotExist:
         return HttpResponse("Eh - history for what storage ??" % pk,status=404,content_type="text/plain")
    context = {
       'title': 'View history',
#       'opts': { 'admin_url': { 'simple_history': 'xxx' } },
    }
    if rev:
      revInfo = storage.history.get(pk = rev)
      historic = revInfo.instance
      form = StorageForm(instance = historic)
      context = {
            'title': 'Historic record',
            'label': revInfo,
            'action': None,
            'is_logged_in': request.user.is_authenticated,
            'user' : request.user,
            'owner' : storage.owner,
            'form':  form,
            'storage':  historic,
            'history': True,
      }
      return render(request, 'storage/crud.html', context)
      # return historyAdmin.history_form_view(request,str(pk),str(rev), context)

    historyAdmin = MySimpleHistoryAdmin(Storage,AdminSite())
    return historyAdmin.history_view(request,str(pk),context)
