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
from simple_history.admin import SimpleHistoryAdmin
from .admin import UfoAdmin

import datetime
import uuid
import logging
import zipfile

import re
from PIL import Image
from resizeimage import resizeimage

logger = logging.getLogger(__name__)

from .models import Ufo
from .forms import UfoForm, NewUfoForm, UfoZipUploadForm

@login_required
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

def create(request):
    form = NewUfoForm(request.POST or None, request.FILES, initial = { 'state': 'UNK' })
    logger.error(request.POST)
    logger.error(request.FILES)
    if form.is_valid():
        try:
            item = form.save(commit=False)

            item.state = 'UNK'
            if not item.description:
                item.description = "Added by {}".format(request.user)

            # item.changeReason("Created by {} through the self-service portal.".format(request.user))
            item.save()
            return redirect('ufo')

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
    item = Ufo.objects.get(pk=pk)
    context = {
        'title': 'Uknown Floating Objects',
        'item': item,
        }
    return render(request, 'ufo/view.html', context)


def modify(request,pk):
    item = Ufo.objects.get(pk=pk)
    form = UfoForm(request.POST or None, instance = item)
    if form.is_valid() and request.POST:
        try:
            item = form.save(commit=False)
            item.changeReason("Changed by {} via self service portal".format(request.user))
            item.save()
        except Exception as e:
            logger.error("Unexpected error during update of ufo: {}".format(e))
        return redirect('ufo')

    context = {
        'title': 'Update an Uknown Floating Objects',
        'form': form,
        'item': item,
        'action': 'Update',
        }

    return render(request, 'ufo/crud.html', context)

def mine(request,pk):
    item = Ufo.objects.get(pk=pk)
    item.changeReason("claimed as 'mine' by {} via self service portal".format(request.user))
    item.owner = request.user
    item.state = 'OK'
    item.save()

    return redirect('ufo')

def delete(request,pk):
    item = Ufo.objects.get(pk=pk)

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

    return redirect('ufo')

def upload_zip(request):
    form = UfoZipUploadForm(request.POST or None, request.FILES)
    if request.method == 'POST':
        if form.is_valid():
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
                    skipped.append("{0}: skipped, does not have an image extension.".format(f))
                    continue

                fp = "ufo/"+str(uuid.uuid4())+"."+extension
                fname = settings.MEDIA_ROOT+"/"+fp
                tname = settings.MEDIA_ROOT+"/small_"+fp

                try:
                  with z.open(f) as fh:
                    with open(fname,"wb+") as dst:
                     dst.write(fh.read())
                except Exception as e:
                    logger.error("Error during zip extract: {}".format(e))
                    skipped.append("{0}: skipped, could not be extracted.".format(f))
                    try:
                      os.remove(fname)
                    except Exception as e:
                      pass
                    continue
                

                try:
                   with open(fname,"rb") as dst:
                     with Image.open(dst) as img:
                       tn = resizeimage.resize_thumbnail(img,[200,200])
                       tn.save(tname,img.format)

                       if img.width > settings.MAX_IMAGE_WIDTH:
                         resizeimage.resize_width(img,1280).save(fname, img.format)
                except Exception as e:
                    skipped.append("{0}: skipped, could not parse the image.".format(f))
                    try:
                      os.remove(fname)
                      os.remove(pname)
                    except Exception as e:
                      pass
                    continue
                         
                ufo = Ufo(description="Auto", image=fp,state='UNK');
                ufo.save()

                lst.append(ufo)
            try:
               os.remove(tmpZip)
            except:
                logger.error("Error during cleanup of {}: {}".format(tmpZip),e)

            return render(request, 'ufo/upload.html', { 
               'action': 'Done', 
               'lst': lst,
               'skipped': skipped,
               })

    return render(request, 'ufo/upload.html', {'form': form, 'action': 'Upload' })
