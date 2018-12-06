from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.http import Http404

from members.models import PermitType,Member,Entitlement,Tag
from .models import Machine,Instruction

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

def details(request,machine_id):
    try:
       machine = Machine.objects.get(pk=machine_id)
    except:
       raise Http404("Machine gone AWOL, sorry")

    lst = {}
    for m in Member.objects.order_by():
       lst[ m.user.username ] = []

       # Does the machine require a form; and does the user have that form on file.
       if machine.requires_form and not m.form_on_file:
          continue

       # Is a permit required ?
       # If not - fall back to a dead normal instruction need.
       if machine.requires_permit: 
           if Entitlement.objects.filter(permit = machine.requires_permit, holder = m.user).count() < 1:
             continue
       else:  
           if machine.requires_instruction and Instruction.objects.filter(machine = machine_id, holder = m.user).count() < 1:
              continue

       for tag in Tag.objects.filter(owner = m):
          lst[ m.user.username ].append(tag.tag)

    context = {
       'machine': machine.name,
       'lst': lst,
    }
    return render(request, 'acl/details.html', context, content_type='text/plain')
