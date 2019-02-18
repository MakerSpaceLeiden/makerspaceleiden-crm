import os
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.template import loader
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.urls import reverse

from django.conf import settings

import logging

from members.models import Tag,User
from acl.models import Machine,Entitlement,PermitType
from selfservice.forms import UserForm, SignUpForm, SignalNotificationSettingsForm
from .models import WiFiNetwork
from .waiverform.waiverform import generate_waiverform_fd
from .aggregator_adapter import get_aggregator_adapter


def sentEmailVerification(request,user,new_email,ccOrNone = None, template='email_verification_email.txt'):
            current_site = get_current_site(request)
            subject = 'Confirm your email adddress ({})'.format(current_site.domain)
            context = {
                'request': request,
                'user': user,
		'new_email': new_email,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': email_check_token.make_token(user),
            }

            msg = render_to_string(template, context)
            EmailMessage(subject, msg, to=[user.email], from_email=settings.DEFAULT_FROM_EMAIL).send()

            if ccOrNone:
                subject = '[spacebot] User {} {} is changing is or her email adddress'.format(user.first_name, user.last_name)
                msg = render_to_string('email_verification_email_inform.txt', context)
                EmailMessage(subject, msg, to=ccOrNone, from_email=settings.DEFAULT_FROM_EMAIL).send()

            return render(request, 'email_verification_email.html')

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.email)

email_check_token = AccountActivationTokenGenerator()
logger = logging.getLogger(__name__)

def index(request):
    context = {
	'title': 'Selfservice',
	'user' : request.user,
	'has_permission': request.user.is_authenticated,
    }
    if (request.user.is_authenticated):
        context['is_logged_in'] = request.user.is_authenticated
        context['member'] = request.user
        context['wifinetworks'] = WiFiNetwork.objects.order_by('network')
    return render(request, 'index.html', context)

@login_required
def pending(request):
    pending = Entitlement.objects.all().filter(active = False).filter(holder__is_active = True)

    es = []
    for p in pending:
        es.append((p.id,p))

    form = forms.Form(request.POST)
    form.fields['entitlement'] = forms.MultipleChoiceField(label='Entitlements',choices=es)
    context = {
	'title': 'Pending entitlements',
	'user' : request.user,
	'has_permission': request.user.is_authenticated,
        'pending': pending,
	'lst': es,
	'form': form,
    }
    if request.method == "POST" and form.is_valid():
      if not request.user.is_staff:
          return HttpResponse("You are propably not an admin ?",status=403,content_type="text/plain")

      for eid in form.cleaned_data['entitlement']:
          e = Entitlement.objects.get(pk=eid)
          e.active = True
          e.changeReason = 'Activated through the self-service interface by {0}'.format(request.user)
          e.save()
      context['saved'] = True

    return render(request, 'pending.html', context)

@login_required
def recordinstructions(request):
    member = request.user

    # keep the option open to `do bulk adds
    members = User.objects.filter(is_active = True).exclude(id = member.id) #.order_by('first_name')

    # Only show machine we are entitled for ourselves.
    #
    machines = Machine.objects.all().filter(requires_permit__isRequiredToOperate__holder=member).filter(Q(requires_permit__permit=None) | Q(requires_permit__permit__isRequiredToOperate__holder=member) | Q(requires_permit = None))

    ps =[]
    for m in members:
      ps.append((m.id,m.first_name +' ' + m.last_name))

    ms = []
    for m in machines:
          ms.append((m.id,m.name))

    form = forms.Form(request.POST) # machines, members)
    form.fields['machine'] = forms.MultipleChoiceField(label='Machine',choices=ms,help_text='Select multiple if so desired')
    form.fields['person'] = forms.ChoiceField(label='Person',choices=ps)

    context = {
        'machines': machines,
        'members': members,
	'title': 'Selfservice - record instructions',
	'is_logged_in': request.user.is_authenticated,
	'user' : request.user,
	'has_permission': True,
	'form': form,
        'lst': ms,
    }

    saved = False
    if request.method == "POST" and form.is_valid():
      context['machines'] = []
      for mid in form.cleaned_data['machine']:
       try:
         m = Machine.objects.get(pk=mid)
         p = User.objects.get(pk=form.cleaned_data['person'])
         i = user=request.user

         pt = None
         if m.requires_permit:
             pt = PermitType.objects.get(pk=m.requires_permit.id)

         # Note: We allow for 'refreshers' -- and rely on the history record.
         #
         created = False
         try:
            record = Entitlement.objects.get(permit=pt, holder=p)
            record.issuer = i
            record.changeReason = 'Updated through the self-service interface by {0}'.format(i)
         except Entitlement.DoesNotExist:
            record = Entitlement.objects.create(permit=pt, holder=p, issuer=i)
            created = True
            record.changeReason = 'Created in the self-service interface by {0}'.format(i)
         except Exception as e:
            logger.error("Something else went wrong during create: {0}".format(e))
            raise e

         if pt and pt.permit:
             # Entitlements that require instruction permits also
             # require a trustee OK. This gets reset on re-intruction.
             #
             record.active = False;
         else:
             record.active = True;

         record.save()

         context["created"] = created
         context['machines'].append(m)
         context['holder'] = p
         context['issuer'] = i

         saved = True
       except Exception as e:
         logger.error("Unexpected error during save of intructions: {0}".format(e))

    context['saved'] = saved

    return render(request, 'record.html', context)

@login_required
def confirmemail(request, uidb64, token, newemail):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if request.user != user:
           return HttpResponse("You can only change your own records.",status=500,content_type="text/plain")
        user.email = newemail
        if email_check_token.check_token(user, token):
           user.email = newemail
           user.email_confirmed = True
           user.save()
        else:
           return HttpResponse("Failed to confirm",status=500,content_type="text/plain")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        # We perhaps should not provide the end user with feedback -- e.g. prentent all
        # went well. As we do not want to function as an oracle.
        #
        logger.error("Something else went wrong in confirm email: {0}".format(e))
        HttpResponse("Something went wrong. Sorry.",status=500,content_type="text/plain")

    # return redirect('userdetails')
    return render(request, 'email_verification_ok.html')


@login_required
def waiverform(request, user_id=None):
    try:
        member = User.objects.get(pk=user_id)
    except ObjectDoesNotExist as e:
        return HttpResponse("User not found", status=404, content_type="text/plain")
    confirmation_url = request.build_absolute_uri(reverse('waiver_confirmation', kwargs=dict(user_id=user_id)))
    fd = generate_waiverform_fd(member.id, f'{member.first_name} {member.last_name}', confirmation_url)
    return HttpResponse(fd.getvalue(), status=200, content_type="application/pdf")


@login_required
def confirm_waiver(request, user_id=None):
    try:
        operator_user = request.user
    except User.DoesNotExist:
        return HttpResponse("You are probably not a member-- admin perhaps?", status=400, content_type="text/plain")

    try:
        member = User.objects.get(pk=user_id)
    except ObjectDoesNotExist as e:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    if not operator_user.is_staff:
        return HttpResponse("You must be staff to confirm a waiver", status=400, content_type="text/plain")

    member.form_on_file = True
    member.save()

    return render(request, 'waiver_confirmation.html', { 'member': member })

@login_required
def telegram_connect(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse("You are probably not a member-- admin perhaps?", status=400, content_type="text/plain")

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist as e:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse("No aggregator configuration found", status=500, content_type="text/plain")

    token = aggregator_adapter.generate_telegram_connect_token(user.id)
    return HttpResponse(token, status=200, content_type="text/plain")


@login_required
def telegram_disconnect(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse("You are probably not a member-- admin perhaps?", status=400, content_type="text/plain")

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist as e:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse("No aggregator configuration found", status=500, content_type="text/plain")

    aggregator_adapter.disconnect_telegram(user.id)
    return render(request, 'telegram_disconnect.html', {
        'title': 'Telegram BOT',
    })


@login_required
def signal_disconnect(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse("You are probably not a member-- admin perhaps?", status=400, content_type="text/plain")

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist as e:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    user.uses_signal = False
    user.save()

    return render(request, 'signal_disconnect.html', {
        'title': 'Signal BOT',
    })

@login_required
def notification_settings(request):
    try:
        user = request.user
    except User.DoesNotExist:
        return HttpResponse("You are probably not a member-- admin perhaps?", status=400, content_type="text/plain")

    try:
        User.objects.get(pk=user.id)
    except ObjectDoesNotExist as e:
        return HttpResponse("User not found", status=404, content_type="text/plain")

    if request.method == "POST":
        user_form = SignalNotificationSettingsForm(request.POST, request.FILES, instance = user)
        if user_form.is_valid():
            user_form.save()
            return redirect('overview', member_id=user.id)

    form = SignalNotificationSettingsForm(instance = user)

    return render(request, 'notification_settings.html', {
        'title': 'Notification Settings',
        'uses_signal': user.phone_number and user.uses_signal,
        'form': form,
        'user': user,
    })


@login_required
def space_state(request):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse("No aggregator configuration found", status=500, content_type="text/plain")
    return render(request, 'space_state.html', aggregator_adapter.fetch_state_space())


@login_required
def userdetails(request):
    try:
       member = request.user
       old_email = "{}".format(member.email)
    except User.DoesNotExist:
       return HttpResponse("You are probably not a member-- admin perhaps?", status=500, content_type="text/plain")

    if request.method == "POST":
       try:
         user = UserForm(request.POST, request.FILES, instance = request.user)
         save_user = user.save(commit=False)
         if user.is_valid():
             new_email = "{}".format(user.cleaned_data['email'])

             save_user.email = old_email
             save_user.changeReason = 'Updated through the self-service interface by {0}'.format(request.user)
             save_user.save()

             user = UserForm(request.POST, instance = save_user)
             for f in user.fields:
               user.fields[f].disabled = True

             if old_email != new_email:
                member.email_confirmed = False
                member.changeReason = "Reset email validation, email changed."
                member.save()
                return sentEmailVerification(request,save_user,new_email, [ old_email, settings.TRUSTEES ])

             return render(request, 'userdetails.html', { 'form' : user, 'saved': True })
       except Exception as e:
         logger.error("Unexpected error during save of user: {0}".format(e))
         return HttpResponse("Unexpected error during save",status=500,content_type="text/plain")

    form = UserForm(instance = request.user)
    context = {
        'title': 'Selfservice - update details',
        'is_logged_in': request.user.is_authenticated,
        'user' : request.user,
        'form': form,
        'has_permission': True,
    }
    return render(request, 'userdetails.html', context)

def signup(request):
    if (request.user.is_authenticated):
       return HttpResponse("You are perhaps logged in already ?",status=500,content_type="text/plain")

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            return sentEmailVerification(request,user,email,[ settings.TRUSTEES ],'signup_email.txt' )

            user = authenticate(email=email, password=raw_password)
            login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

class AmnestyForm(forms.Form):

    def __init__(self, *args, **kwargs):
        machines = kwargs.pop('machines')
        super(AmnestyForm, self).__init__(*args, **kwargs)
        for m in machines:
            self.fields['machine_%s' % m.id ] = forms.BooleanField(label=m.name, required=False)

@login_required
def amnesty(request):
    machines = Machine.objects.exclude(requires_permit = None)
    machines_entitled = Machine.objects.all().filter(requires_permit__isRequiredToOperate__holder=request.user)

    context = { 'title': 'Amnesty', 'saved': False }

    form = AmnestyForm(request.POST or None, machines=machines)
    if form.is_valid():
        permits = []
        for m in machines:
            if not form.cleaned_data['machine_%s' % m.id]:
                continue
            if m in machines_entitled:
                continue
            if not m.requires_permit or m.requires_permit in permits:
                  continue
            permits.append(m.requires_permit)
        for p in permits:
            e,created = Entitlement.objects.get_or_create(holder = request.user,
                    issuer = request.user, permit = p);
            if created:
               e.changeReason = 'Added through the grand amnesty interface by {0}'.format(request.user)
               e.active = True
               e.save()
               context['saved'] = True
            # return redirect('userdetails')

    for m in machines_entitled:
         form.fields['machine_%s' % m.id ].initial = True
         form.fields['machine_%s' % m.id ].disabled = True
         form.fields['machine_%s' % m.id ].help_text = 'Already listed - cannot be edited.'

    context['form'] = form

    return render(request, 'amnesty.html', context)
