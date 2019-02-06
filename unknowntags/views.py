from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Unknowntag
from members.models import Tag,User
from acl.models import Entitlement,PermitType

from .forms import SelectUserForm, SelectTagForm

from makerspaceleiden.decorators import superuser_or_bearer_required

import logging
import datetime
import re

logger = logging.getLogger(__name__)

@csrf_exempt
@superuser_or_bearer_required
def unknowntag(request):
  if request.POST:
     try:
         tag = request.POST.get("tag")
         tag = '-'.join([ b for b in re.compile('[^0-9]+').split(tag.upper()) if b is not None and b is not '' and int(b) >=0 and int(b) < 256])
         if len(tag) < 4:
             return HttpResponse("Unhappy",status=500,content_type="text/plain")
         ut, created = Unknowntag.objects.get_or_create(tag = tag)
         # ut.save()
         if created:
              logger.debug("Added tag {} to the unknown tags list.".format(tag))
              return HttpResponse("OK",status=200,content_type="text/plain")

         return HttpResponse("Already have that tag",status=500,content_type="text/plain")
     except Exception as e:
         logger.error("Unexpected error during unknown tag register: {}".format(e))
     return HttpResponse("Unhappy",status=500,content_type="text/plain")

  return render(request, 'unknowntags.txt', { 
               'items': Unknowntag.objects.all().order_by('-last_used'),
         }, content_type="text/plain")

@login_required
def unknowntags(request):
  return render(request, 'unknowntags.html', { 
               'items': Unknowntag.objects.all().order_by('-last_used'),
		'user': request.user,
         })

@login_required
def addmembertounknowntag(request, user_id = None):
  if not request.user.is_superuser:
         return HttpResponse("XS denied",status=403,content_type="text/plain")


  if request.POST:
    form = SelectTagForm(request.POST)
    if form.is_valid():
        try:
             user = User.objects.get(pk=user_id)
             tag = form.cleaned_data.get('tag')
        except:
             return HttpResponse("Unknown tag or user gone awol. Drat.",status=500,content_type="text/plain")

        return link_tag_user(request,form,tag,user)

  form = SelectTagForm()
  return render(request, 'crud.html', { 'title': 'Select Tag', 'form': form, 'action': 'update' })
   
@login_required
def addunknowntagtomember(request, tag_id = None):
  if not request.user.is_superuser:
         return HttpResponse("XS denied",status=403,content_type="text/plain")

  try:
      tag= Unknowntag.objects.get(pk=tag_id)
  except:
      return HttpResponse("Unknown tag gone awol. Drat.",status=500,content_type="text/plain")

  try:
      existing_tag = Tag.objects.get(tag=tag['tag'])
      return HttpResponse("Tag already in use",status=500,content_type="text/plain")
  except:
      pass

  if request.POST:
    form = SelectUserForm(request.POST)
    if form.is_valid():
       return link_tag_user(request,form,tag,form.cleaned_data.get('user'))

  form = SelectUserForm()
  return render(request, 'crud.html', { 'title': 'Select User', 'form': form, 'action': 'update' })

def link_tag_user(request, form, tag, user):
    try:
          print("Linking {} userid={}/{} ".format(tag.tag,user.id,user))
          newtag = Tag.objects.create(tag=tag.tag, owner = user,
                 description="The card that was wdded on {} by {}".format(datetime.date.today(), request.user))
          newtag.changeReason = "Linked by {} ".format(request.user)
          newtag.save()
          tag.delete()

          if form.cleaned_data.get('activate_doors'):
              doors= PermitType.objects.get(pk=settings.DOORS)
              e,created = Entitlement.objects.get_or_create(active=True, permit = doors, holder = user, issuer = request.user)
              if created:
                  e.changeReason = "Auto created during linking of unknown tag by {}".format(request.user)
                  e.save()

    except Exception as e:
          logger.error("Failed to link tag: {}".format(e))
          return HttpResponse("Save tag gone awol. Drat.",status=500,content_type="text/plain")
 
    return redirect('index')
