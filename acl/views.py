from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate
from django.conf import settings
from django.shortcuts import redirect

from members.models import PermitType,Member,Entitlement,Tag
from .models import Machine,Instruction

def matrix_mm(machine,mbr):
       out = { 'xs' : False, 'tags' : [] }

       # Does the machine require a form; and does the user have that form on file.
       if machine.requires_form and not mbr.form_on_file:
          return

       # Is a permit required ?
       # If not - fall back to a dead normal instruction need.
       if machine.requires_permit: 
           if Entitlement.objects.filter(permit = machine.requires_permit, holder = mbr.user).count() < 1:
             return
       else:  
           if machine.requires_instruction and Instruction.objects.filter(machine = machine.id, holder = mbr).count() < 1:
             return

       for tag in Tag.objects.filter(owner = mbr):
          out['tags'].append(tag.tag)
       
       out['xs'] = True

       return out 

def matrix_m(machine):
    lst = {}
    for mbr in Member.objects.order_by():
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
       'members': Member.objects.order_by(),
       'machines': machines,
       'lst': lst,
    }
    return render(request, 'acl/matrix.html', context)

@login_required
def member_overview(request,member_id):
    member = Member.objects.get(pk=member_id)
    machines = Machine.objects.order_by()
    lst = {}
    for mchn in machines:
       lst[ mchn.name ] = matrix_mm(mchn, member)

    context = {
       'title': "XS matrix " + member.user.first_name + ' ' + member.user.last_name,
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
