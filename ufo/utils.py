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

def emailUfoInfo(itemsToAttachImage, template, toinform = [], context = {}):
    to = {}
    if settings.ALSO_INFORM_EMAIL_ADDRESSES:
       toinform.extend(settings.ALSO_INFORM_EMAIL_ADDRESSES)

    for person in toinform:
       to[person]=True

    # We use a dict rather than an array to prune any duplicates.
    to = to.keys()

    context['base' ] =  settings.BASE
    context['items'] = itemsToAttachImage
    context['count'] = len(itemsToAttachImage)

    part2 = None

    if len(itemsToAttachImage)> 1:
          msg = MIMEMultipart('alternative')
          subject = render_to_string('ufo/{}_bulk_subject.txt'.format(template), context)

          part1 = MIMEText(render_to_string('ufo/{}_bulk.txt'.format(template), context) , 'plain')
          part2 = MIMEMultipart('related')
          part2.attach(MIMEText(render_to_string('ufo/{}_bulk.html'.format(template), context) , 'html'))

          for i in itemsToAttachImage:
             ext = i.image.name.split('.')[-1]
             attachment = MIMEImage(i.image.thumbnail.read(), "image/"+ext)
             attachment.add_header('Content-ID',str(i.pk))
             attachment.add_header('Content-Disposition', 'inline; filename="' + i.image.name +'"')
             part2.attach(attachment)
    else:
          msg = MIMEMultipart('mixed')
          subject = render_to_string('ufo/{}_subject.txt'.format(template), context)

          part1 = MIMEText(render_to_string('ufo/{}.txt'.format(template), context), 'plain')
          part2 = MIMEMultipart('mixed')

          ext = itemsToAttachImage.image.name.split('.')[-1]
          attachment = MIMEImage(itemsToAttachImage.first.image.medium.read(), ext)
          attachment.add_header('Content-ID',str(item.first.pk))
          part2.attach(attachment)

    msg.attach(part1)
    msg.attach(part2)

    email = EmailMessage(subject.strip(), None, to=to, from_email=settings.DEFAULT_FROM_EMAIL)
    email.attach(msg)
    email.send()
