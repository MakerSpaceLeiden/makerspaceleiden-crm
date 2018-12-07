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

import logging
logger = logging.getLogger(__name__)


from members.models import PermitType,Member,Entitlement,Tag
from acl.models import Machine,Instruction

def index(request):
    context = {
	'title': 'Selfservice',
	'user' : request.user,
	'is_logged_in': request.user.is_authenticated,
	'has_permission': True,
    }
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
    machines = Machine.objects.filter(instruction__holder=request.user.id)
    members =  Member.objects.exclude(user = request.user.id).order_by('user__first_name')
 
    ps =[]
    for m in members:
      ps.append((m.id,m.user.first_name +' ' + m.user.last_name))
    ms = []
    for m in machines:
      ms.append((m.id,m.name))
  
    form = forms.Form(request.POST) # machines, members)
    form.fields['machine'] =  forms.ChoiceField(label='Machine',choices=ms)
    form.fields['person'] =  forms.ChoiceField(label='Person',choices=ps)

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

@login_required
def saveinstructions(request):
    # add issuer!
    context = {
	'user' : request.user,
    }
    return render(request, 'ok.html', context)
 
