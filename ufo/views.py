from django.shortcuts import render
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
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import datetime
import uuid
import zipfile
import os
import re

import logging
logger = logging.getLogger(__name__)

from .models import Ufo
from .admin import UfoAdmin
from .forms import UfoForm, NewUfoForm, UfoZipUploadForm
from members.models import User

# Note - we do this here; rather than in the model its save() - as this
# lets admins change things through the database interface silently. 
# Which can help when sheparding the community.
#
def alertOwnersToChange(itemOrItems, userThatMadeTheChange = None, toinform = []):

    to = {}
    if userThatMadeTheChange:
       to[ userThatMadeTheChange.email ] = True 
    
    if settings.ALSO_INFORM_EMAIL_ADDRESSES:
       toinform.extend(settings.ALSO_INFORM_EMAIL_ADDRESSES)

    for person in toinform:
        if person and isinstance(person,User):
            to[person.email]=True
        else:
            to[person]=True

    # We use a dict rather than an array to prune any duplicates.
    to = to.keys()

    context = {
           'user': userThatMadeTheChange,
           'base': settings.BASE,
    }
    part2 = None

    if isinstance(itemOrItems,list):
          context['items'] = itemOrItems
          subject = "[makerbot] Upload of %d UFOs" % len(itemOrItems)

          part1 = MIMEText(render_to_string('ufo/email_notification_bulk.txt', context) , 'plain')
          part2 = MIMEMultipart('related')
          part2.attach(MIMEText(render_to_string('ufo/email_notification_bulk.html', context) , 'html'))
    else:
          context['item'] = itemOrItems
          subject = "[makerbot] Change to an UFO: %s" % itemOrItems.description
          part1 = MIMEText(render_to_string('ufo/email_notification.txt', context), 'plain')
          part2 = MIMEMultipart('mixed')

    # Note that we want the images to be (much) smaller if we are doing
    # lot of them (e.g. in case of a zip upload) - than if it is just
    # a single one.
    #
    if isinstance(itemOrItems,list):
       msg = MIMEMultipart('alternative')
       for i in itemOrItems:
           ext = i.image.name.split('.')[-1]
           attachment = MIMEImage(i.image.thumbnail.read(), "image/"+ext)
           attachment.add_header('Content-ID',str(i.pk))
           attachment.add_header('Content-Disposition', 'inline; filename="' + i.image.name +'"')
           part2.attach(attachment)
           # email.attach(i.image.name, i.image.thumbnail.read(), "image/"+ext)
    else:
       msg = MIMEMultipart('mixed')
       ext = itemOrItems.image.name.split('.')[-1]
       attachment = MIMEImage(itemOrItems.image.medium.read(), ext)
       attachment.add_header('Content-ID',str(itemOrItems.pk))
       part2.attach(attachment)

    msg.attach(part1)
    msg.attach(part2)

    email = EmailMessage(subject, None, to=to, from_email=settings.DEFAULT_FROM_EMAIL)
    email.attach(msg)
    email.send()

def ufo_redirect(pk = None):
    url = reverse('ufo')
    if pk:
      url = '%s#%d' % (url, pk)
    return redirect(url)


def index(request,days=30):
    lst = Ufo.objects.all()
    if days > 0:
        tooOld = datetime.date.today() - datetime.timedelta(days=days)
        lst = lst.filter(Q(lastChange__gte=tooOld) | Q(state = 'UNK'))
    context = {
        'title': 'Uknown Floating Objects',
        'lst': lst,
        'days': days,
       }
    return render(request, 'ufo/index.html', context)

@login_required
def create(request):
    form = NewUfoForm(request.POST or None, request.FILES, initial = { 'state': 'UNK' })
    if form.is_valid():
        try:
            item = form.save(commit = False)

            item.state = 'UNK'
            if not item.description:
                item.description = "Added by {}".format(request.user)

            item.changeReason = "Created by {} through the self-service portal.".format(request.user)
            item.save()

            alertOwnersToChange(item, request.user, [ item.owner ])
            return ufo_redirect(item.id)

        except Exception as e:
            logger.error("Unexpected error during initial save of new ufo: {}".format(e))

        return HttpResponse("Something went wrong ??",status=500,content_type="text/plain")

    context = {
        'title': 'Add an Uknown Floating Objects',
        'form': form,
        'action': 'Add',
        }
    return render(request, 'ufo/crud.html', context)

def show(request,pk):
    try:
       item = Ufo.objects.get(pk=pk)
    except ObjectDoesNotExist as e:
        return HttpResponse("UFO not found",status=404,content_type="text/plain")

    context = {
        'title': 'Uknown Floating Objects',
        'item': item,
        }
    return render(request, 'ufo/view.html', context)

@login_required
def modify(request,pk):
    try:
        oitem = Ufo.objects.get(pk=pk)
    except ObjectDoesNotExist as e:
        return HttpResponse("UFO not found",status=404,content_type="text/plain")
    toinform = [ oitem.owner ]

    context = {
        'title': 'Update an Uknown Floating Objects',
        'action': 'Update',
	'item': oitem,
        }
    if request.POST:
     form = UfoForm(request.POST or None, request.FILES, instance = oitem)
     if form.is_valid() and request.POST:
        try:
            item = form.save(commit = False)
            item.changeReason = "Changed by {} via self service portal".format(request.user)
            item.save()
        except Exception as e:
            logger.error("Unexpected error during update of ufo: {}".format(e))

        toinform.append(item.owner)
 
        alertOwnersToChange(item, request.user, toinform )

        context['item']=item

        return ufo_redirect(pk)

    form = UfoForm(instance = oitem)
    context['form'] = form

    return render(request, 'ufo/crud.html', context)

@login_required
def mine(request,pk):
    try:
        item = Ufo.objects.get(pk=pk)
    except ObjectDoesNotExist as e:
        return HttpResponse("UFO not found",status=404,content_type="text/plain")

    item.changeReason = "claimed as 'mine' by {} via self service portal".format(request.user)
    if item.owner != request.user:
        alertOwnersToChange(item, request.user, [ item.owner ])
    item.owner = request.user
    item.state = 'OK'
    item.save()

    return ufo_redirect(pk)

@login_required
# Limit this to admins ?
def delete(request,pk):
    try:
       item = Ufo.objects.get(pk=pk)
    except ObjectDoesNotExist as e:
       return HttpResponse("UFO not found",status=404,content_type="text/plain")


    form = UfoForm(request.POST or None, instance = item)
    for f in form.fields:
        form.fields[f].disabled = True

    if not request.POST:
         context = {
            'title': 'Confirm delete of this UFO',
            'label': 'Confirm delete of this UFO',
            'action': 'Delete',
            'is_logged_in': request.user.is_authenticated,
            'user' : request.user,
            'form':  form,
            'item': item,
            'delete': True,
         }
         return render(request, 'ufo/crud.html', context)

    if not form.is_valid():
         return HttpResponse("Eh - confused ?!",status=403,content_type="text/plain")

    try:
       item.changeReason = 'Deleted via the self-service interface by {0}'.format(request.user)
       item.save()
       item.delete()
    except Exception as e:
         logger.error("Unexpected error during delete of item: {0}".format(e))
         return HttpResponse("Box fail",status=400,content_type="text/plain")

    return ufo_redirect()

@login_required
def upload_zip(request):
    form = UfoZipUploadForm(request.POST or None, request.FILES)
    if request.method == 'POST':
        if form.is_valid() and 'zipfile' in request.FILES:
            if request.FILES['zipfile'].size > settings.MAX_ZIPFILE:
                return HttpResponse("Upload too large",status=500,content_type="text/plain")

            tmpZip = settings.MEDIA_ROOT+"/ufozip-"+str(uuid.uuid4())
            with open(tmpZip,'wb+') as dst:
                for c in request.FILES['zipfile'].chunks():
                    dst.write(c)

            skipped = []
            lst = []
            with zipfile.ZipFile(tmpZip, 'r') as z:
              for zi in z.infolist():
                if zi.is_dir():
                    skipped.append("{0}: skipped, directory".format(f))
                    continue
                f = zi.filename
                if re.match("\..*",f):
                    skipped.append("{0}: skipped, hidden file".format(f))
                    continue
                if re.match(".*/\.",f):
                    skipped.append("{0}: skipped, hidden file".format(f))
                    continue
                if zi.file_size < settings.MIN_IMAGE_SIZE:
                    skipped.append("{0}: skipped, too small".format(f))
                    continue
                if zi.file_size > settings.MAX_IMAGE_SIZE:
                    skipped.append("{0}: skipped, too large".format(f))
                    continue

                extension = 'raw'
                if re.match(".*\.(jpg|jpeg)$", f,re.IGNORECASE):
                    extension = 'jpg'
                elif re.match(".*\.(png)$", f,re.IGNORECASE):
                    extension = 'png'
                else:
                    skipped.append("{0}: skipped, does not have an image extension such as .jp(e)g or .png.".format(f))
                    continue

                ufo = Ufo(description="Auto upload",state='UNK')

                try:
                  with z.open(f) as fh:
                     fp = str(uuid.uuid4())+"."+extension
                     ufo.image.save(fp,fh)
                except Exception as e:
                    logger.error("Error during zip extract: {}".format(e))
                    skipped.append("{0}: skipped, could not be extracted.".format(f))
                    continue

                for f in [ 'description', 'deadline', 'dispose_by_date' ]:
                    if form.cleaned_data[f]:
                        setattr(ufo, f, form.cleaned_data[f])

                ufo.changeReason = "Part of a bulk upload by {}".format(request.user)
                ufo.save()

                lst.append(ufo)
            try:
               os.remove(tmpZip)
            except:
                logger.error("Error during cleanup of {}: {}".format(tmpZip,e))

            if lst:
                alertOwnersToChange(lst, request.user, [ request.user ])

            return render(request, 'ufo/upload.html', { 
               'action': 'Done', 
               'lst': lst,
               'skipped': skipped,
               })

    return render(request, 'ufo/upload.html', {'form': form, 'action': 'Upload' })
