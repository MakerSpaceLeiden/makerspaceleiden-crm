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

from members.models import Tag,User
from .models import Machine,Entitlement,PermitType
from storage.models import Storage
from memberbox.models import Memberbox

def matrix_mm(machine,mbr):
       out = { 'xs' : False, 'instructions_needed' : False, 'tags' : [] }
       out['mid'] = machine.id

       out['requires_instruction'] = machine.requires_instruction
       out['requires_permit'] = machine.requires_permit
       out['requires_form'] = machine.requires_form

       # Does the machine require a form; and does the user have that form on file.
       if machine.requires_form and not mbr.form_on_file:
          return out

       xs = True
       if machine.requires_permit: 
           ents = Entitlement.objects.filter(permit = machine.requires_permit, holder = mbr)
           if ents.count() < 1:
             return out

           for e in ents:
               out['has_permit'] = True
               if e.active == False:
                    xs = False

       for tag in Tag.objects.filter(owner = mbr):
          out['tags'].append(tag.tag)
       
       out['activated'] = xs
       out['xs'] = xs

       return out 

def matrix_m(machine):
    lst = {}
    for mbr in User.objects.order_by():
       lst[ mbr ] = matrix_mm(machine,mbr)
  
    return lst 

@login_required
def api_index(request):
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
def machine_overview(request, machine_id = None):
    instructors = []
    machines = Machine.objects.order_by('name')
    if machine_id:
        machines = machines.filter(pk = machine_id)
        machine = machines.first()
        permit = machine.requires_permit
        if permit:
            permit = PermitType.objects.get(pk = permit.id)
            if permit.permit:
                instructors = Entitlement.objects.filter(permit=permit)
    lst = {}
    for mchn in machines:
       lst[ mchn.name ] = matrix_m(mchn)

    context = {
       'members': User.objects.order_by('first_name'),
       'machines': machines,
       'lst': lst,
       'instructors': instructors,
    }
    return render(request, 'acl/matrix.html', context)

@login_required
def members(request):
    members = User.objects.order_by('first_name')

    context = {
       'title': "Members list",
       'members': members,
    }
    return render(request, 'acl/members.html', context)

@login_required
def member_overview(request,member_id = None):
    member = User.objects.get(pk=member_id)
    machines = Machine.objects.order_by()
    boxes = Memberbox.objects.all().filter(owner = member)
    storage = Storage.objects.all().filter(owner = member)
    normal_permits = {}
    for m in machines:
        normal_permits[ m.requires_permit ] = True

    specials = []
    for e in Entitlement.objects.all().filter(holder = member):
        if not e.permit in normal_permits:
            specials.append(e)

    lst = {}
    for mchn in machines:
       lst[ mchn.name ] = matrix_mm(mchn, member)

    context = {
       'title': "XS matrix " + member.first_name + ' ' + member.last_name,
       'member': member,
       'machines': machines,
       'storage': storage,
       'boxes': boxes,
       'lst': lst,
       'permits': specials,
    }
    return render(request, 'acl/member_overview.html', context)

@login_required
def api_details(request,machine_id):
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
    holders = User.objects.all().filter(form_on_file = tof).filter(isGivenTo__permit__has_permit__requires_form = True).distinct()
    return holders

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
    # people_with_forms = User.objects.all().filter(form_on_file = True)
    context = {
	'title': 'Filed forms',
	'desc': 'Forms on file for people that also had instruction on something',
	'amiss': missing(True)
    }
    return render(request, 'acl/missing.html',context)
