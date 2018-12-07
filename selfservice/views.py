from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django import forms
from django.forms import ModelForm
from django.contrib.auth.models import User

import logging
logger = logging.getLogger(__name__)


from members.models import PermitType,Member,Entitlement,Tag
from acl.models import Machine,Instruction

def index(request):
    context = {
	'title': 'Selfservice',
	'user' : request.user,
	'has_permission': True,
    }
    if (request.user.is_authenticated):
        context['is_logged_in'] = request.user.is_authenticated
        try:
           context['member'] = Member.objects.get(user = request.user)
        except Member.DoesNotExist:
           pass
    return render(request, 'index.html', context)

@login_required
def selfupdate(request):
    context = {
	'title': 'Selfservice - update your record',
	'is_logged_in': request.user.is_authenticated,
	'user' : request.user,
	'has_permission': True,
    }
    return render(request, 'update.html', context)

@login_required
def recordinstructions(request):
    try:
       member = Member.objects.get(user = request.user)
    except Member.DoesNotExist:
       return HttpResponse("You are propably not a member-- admin perhaps?",status=500,content_type="text/plain")

    machines = Machine.objects.filter(instruction__holder=member)
    members =  Member.objects.exclude(user = request.user.id).order_by('user__first_name')
 
    ps =[]
    for m in members:
      ps.append((m.id,m.user.first_name +' ' + m.user.last_name))
    ms = []
    for m in machines:
      ms.append((m.id,m.name))
  
    form = forms.Form(request.POST) # machines, members)
    form.fields['machine'] = forms.ChoiceField(label='Machine',choices=ms)
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
       try:  
         m = Machine.objects.get(pk=form.cleaned_data['machine'])
         p = Member.objects.get(pk=form.cleaned_data['person'])
         i = Member.objects.get(user=request.user.id)

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
         context['machine'] = m
         context['holder'] = p
         context['issuer'] = i

         saved = True
       except Exception as e:
         logger.error("Unexpected error during save of intructions: {0}".format(e))

    context['saved'] = saved
   
    return render(request, 'record.html', context)

class UserForm(ModelForm):
    class Meta:
       model = User
       fields = [ 'first_name', 'last_name', 'email' ]

@login_required
def userdetails(request):
    try:
       member = Member.objects.get(user = request.user)
    except Member.DoesNotExist:
       return HttpResponse("You are propably not a member-- admin perhaps?",status=500,content_type="text/plain")

    if request.method == "POST":
       try:
         user = UserForm(request.POST, instance = request.user) 
         if user.is_valid():
             user.changeReason = 'Updated through the self-service interface by {0}'.format(request.user)
             user.save()
             for f in user.fields:
               user.fields[f].disabled = True
             request.user = user
             return render(request, 'userdetails.html', { 'form' : user, 'saved': True })
       except Exception as e:
         logger.error("Unexpected error during save of user: {0}".format(e))

    form = UserForm(instance = request.user)
    return render(request, 'userdetails.html', { 'form' : form })

