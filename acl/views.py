from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django import forms
from django.forms import ModelForm

from members.models import PermitType,Entitlement,Tag,User
from .models import Machine,Instruction

def matrix_mm(machine,mbr):
       out = { 'xs' : False, 'instructions_needed' : False, 'tags' : [] }

       out['requires_instruction'] = machine.requires_instruction
       out['requires_permit'] = machine.requires_permit
       out['requires_form'] = machine.requires_form

       # Does the machine require a form; and does the user have that form on file.
       if machine.requires_form and not mbr.form_on_file:
          return out

       # Is a permit required ?
       # If not - fall back to a dead normal instruction need.
       if machine.requires_permit: 
           if Entitlement.objects.filter(permit = machine.requires_permit, holder = mbr).count() < 1:
             return out
       else:  
           if machine.requires_instruction and Instruction.objects.filter(machine = machine.id, holder = mbr).count() < 1:
             return out

       for tag in Tag.objects.filter(owner = mbr):
          out['tags'].append(tag.tag)
       
       out['xs'] = True

       return out 

def matrix_m(machine):
    lst = {}
    for mbr in User.objects.order_by():
       lst[ mbr ] = matrix_mm(machine,mbr)
  
    return lst 

@login_required
def index(request):
    lst = Machine.objects.order_by()
    perms = {}
    instructions= []
    ffa = []
    for m in lst:
       if m.requires_permit:
          if not m.requires_permit.name in perms:
              perms[ m.requires_permit.name ] = []
          perms[ m.requires_permit.name ].append(m)
       else:
         if m.requires_instruction:
            instructions.append(m)
         else:
            ffa.append(m)

    context = {
        'lst': lst,
        'perms': perms,
	'instructions': instructions,
	'freeforall': ffa,
    }
    return render(request, 'acl/index.html', context)

@login_required
def overview(request):
    machines = Machine.objects.order_by()
    lst = {}
    for mchn in machines:
       lst[ mchn.name ] = matrix_m(mchn)

    context = {
       'members': User.objects.order_by(),
       'machines': machines,
       'lst': lst,
    }
    return render(request, 'acl/matrix.html', context)

@login_required
def member_overview(request,member_id):
    member = User.objects.get(pk=member_id)
    machines = Machine.objects.order_by()
    lst = {}
    for mchn in machines:
       lst[ mchn.name ] = matrix_mm(mchn, member)

    context = {
       'title': "XS matrix " + member.first_name + ' ' + member.last_name,
       'member': member,
       'machines': machines,
       'lst': lst,
    }
    return render(request, 'acl/member_overview.html', context)

@login_required
def details(request,machine_id):
    try:
       machine = Machine.objects.get(pk=machine_id)
    except:
       raise Http404("Machine gone AWOL, sorry")

    context = {
       'machine': machine.name,
       'lst': matrix_m(machine)
    }
    return render(request, 'acl/details.txt', context, content_type='text/plain')

def missing(tof):
    relevant_machines = Machine.objects.filter(requires_form = True)
    relevant_permits = {}
    permits = PermitType.objects.all()
    for p in permits:
      for m in permits:
         if m.requires_permit == p.name:
            relevant_permits[ p.name ] = 1

    print(relevant_permits)

    entitlements = Entitlement.objects.filter(holder__form_on_file = True)
    missing = {}
    for e in entitlements:
      holder = e.holder
      if not e.permit.name in relevant_permits:
        continue
      if not holder in missing:
        missing[ holder ] = []
      missing[ holder ].append(e.permit)

    return missing

@login_required
def missing_forms(request):
    context = {
	'title': 'Missing forms',
	'desc': 'Missing forms (of people who had instruction on a machine that needs it).',
	'amiss': missing(False)
    }
    return render(request, 'acl/missing.html',context)

@login_required
def filed_forms(request):
    context = {
	'title': 'Filed forms',
	'desc': 'Forms on file for people that also had instruction on something',
	'amiss': missing(True)
    }
    return render(request, 'acl/missing.html',context)
