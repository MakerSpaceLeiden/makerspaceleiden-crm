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
import logging


from members.models import PermitType,Entitlement,Tag,User
from acl.models import Machine,Instruction
from selfservice.forms import UserForm, SignUpForm
from .models import WiFiNetwork

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
def recordinstructions(request):
    try:
       member = request.user
    except User.DoesNotExist:
       return HttpResponse("You are propably not a member-- admin perhaps?",status=500,content_type="text/plain")

    machines = Machine.objects.filter(instruction__holder=member)
    members = User.objects.exclude(id = member.id) #.order_by('first_name')

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
    }

    saved = False
    if request.method == "POST" and form.is_valid():
      context['machines'] = []
      for mid in form.cleaned_data['machine']:
       try:  
         m = Machine.objects.get(pk=mid)
         p = User.objects.get(pk=form.cleaned_data['person'])
         i = user=request.user.id

         created = False

         # We allow for 'refreshers' -- and rely on the history record.
         try:
           record = Instruction.objects.get(machine=m, holder=p)
           record.changeReason = 'Updated through the self-service interface by {0}'.format(i)
           record.issuer = i
           record.save()
         except Instruction.DoesNotExist:
           record = Instruction(machine=m, holder=p, issuer=i)
           record.changeReason = 'Created in the self-service interface by {0}'.format(i)
           record.save()
           created = True

         context["created"] = created
         context['machines'].append(m)
         context['holder'] = p
         context['issuer'] = i

         saved = True
       except Exception as e:
         logger.error("Unexpected error during save of intructions: {0}".format(e))

    context['saved'] = saved
   
    return render(request, 'record.html', context)

def sentEmailVerification(request,user,new_email):
            current_site = get_current_site(request)
            subject = 'Confirm your email adddress ({})'.format(current_site.domain)
            user.email = new_email
            message = render_to_string('email_verification_email.txt', {
                'request': request,
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': email_check_token.make_token(user),
            })
            user.email_user(subject, message)
            return render(request, 'email_verification_email.html')

@login_required
def confirmemail(request, uidb64, token, newemail):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if request.user != user:
           return HttpResponse("You can only change your own records.",status=500,content_type="text/plain")
        member = user.member
        user.email = newemail
        if email_check_token.check_token(user, token):
           user.email = newemail
           user.save()
           user.member.email_confirmed = True
           member.save()
        else:
           return HttpResponse("Failed to confirm",status=500,content_type="text/plain")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, 'email_verification_ok.html')

    # return redirect('userdetails')
    return render(request, 'email_verification_ok.html')

@login_required
def userdetails(request):
    try:
       member = request.user
    except User.DoesNotExist:
       return HttpResponse("You are propably not a member-- admin perhaps?",status=500,content_type="text/plain")

    if request.method == "POST":
       try:
         user = UserForm(request.POST, instance = request.user) 
         save_user = user.save(commit=False)
         if user.is_valid():
             old_email = "{}".format(member.email)
             new_email = "{}".format(user.cleaned_data['email'])

             save_user.email = old_email
             save_user.changeReason = 'Updated through the self-service interface by {0}'.format(request.user)
             save_user.save()

             for f in user.fields:
               user.fields[f].disabled = True
             request.user = user

             if old_email != new_email:
                member.email_confirmed = False
                member.changeReason = "Reset email validation flag as the email was changed from {} to {} by the user (self service)".format(old_email, new_email)
                member.save()
                return sentEmailVerification(request,save_user,new_email)

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
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})
