from django.shortcuts import render,redirect

from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import EmailMessage

from django.template import loader
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.utils import IntegrityError

from .forms import NewUserForm

from acl.models import Entitlement,PermitType
from members.models import Tag,User,clean_tag_string

import logging
import datetime
import re
logger = logging.getLogger(__name__)

@login_required
def index(request):
    lst = Entitlement.objects.order_by('holder__id')
    agg = {}
    perms = {}
    output = ''
    for e in lst:
      if not e.holder in agg:
        agg[e.holder ] = {}
      perms[ e.permit.name ] = 1
      agg[ e.holder ][e.permit.name] = 1

    context = {
        'agg': agg,
        'perms': perms,
    }
    return render(request, 'members/index.html', context)

@login_required
def newmember(request):
    if not request.user.is_superuser:
            return HttpResponse("XS denied",status=403,content_type="text/plain")

    if request.POST:
        form = NewUserForm(request.POST)
        if form.is_valid():
          try:
             email = form.cleaned_data.get('email')
             tag = form.cleaned_data.get('tag')
             newmember = User.objects.create_user(
                 email = email,
                 first_name = form.cleaned_data.get('first_name'),
                 last_name = form.cleaned_data.get('last_name'),
             )

             # Do not set this - it silently blocks the invite mails deep in PasswordResetForm.
             #
             # newmember.set_unusable_password()
             #
             newmember.set_password(  User.objects.make_random_password() )

             if form.cleaned_data.get('phone_number'):
                 newmember.phone_number = form.cleaned_data.get('phone_number')
             newmember.changeReason = "Added by {} with the newnmeber signup form".format(request.user)
             newmember.save()

             # sanity check.
             newmember = User.objects.get(email = email)

             # Wire up the tag if one was provided.

             if form.cleaned_data.get('tag'):
                tag.reassing_to_user(
                        newmember, 
                        request.user, 
                        activate = form.cleaned_data.get('activate_doors')
                )

             # Send welcome email.
             form = PasswordResetForm({'email': newmember.email})
             if not form.is_valid():
                raise Exception("Internal issue")
             form.save(
                      from_email=settings.DEFAULT_FROM_EMAIL, 
                      email_template_name='members/email_newmembers_invite.txt',
                      subject_template_name='members/email_newmembers_invite_subject.txt',
             )
             return redirect('index')
          except IntegrityError as e:
             logger.error("Failed to create user : {}".format(e))
             return HttpResponse("Create gone wrong. Was that email or name already added ?",status=500,content_type="text/plain")
          except Exception as e:
             logger.error("Failed to create user : {}".format(e))
             return HttpResponse("Create gone wrong. Drat.",status=500,content_type="text/plain")
        else:
          logger.debug("Form not valid")

    context = {
          'label': 'Add a new member',
          'title': 'New Member',
          'action': 'Invite',
    }
    context['form'] = NewUserForm()
    return render(request, 'members/newmember.html', context)

  

