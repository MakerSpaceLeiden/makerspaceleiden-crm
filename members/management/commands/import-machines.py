from django.core.management.base import BaseCommand, CommandError

from simple_history.models import HistoricalRecords
from members.models import User
from members.models import Tag,User
from acl.models import Machine,Location,PermitType,Entitlement
from memberbox.models import Memberbox
from storage.models import Storage

import sys,os
''' 
Expert a file like

# Name,instruction-req,permit-req,permit-type,description,location
3 Ton Pers,0,0,,3 Ton tandheugelpers,Metalshop
12 Ton hydraulic pers,1,0,,12 Ton hydraulic pers,Metalshop
3D-printer,1,0,,3D-printer,Frontroom
metalmill,1,1,,Abene VHF3 Metaalfrees machine,Metalshop
mitresaw,1,0,,AfkortZaag,Woodshop
Borgringentangen,0,0,,Borgringentangen,Red Cabinet Metalshop
Combi-tacker,0,0,,Combi-tacker,Woodshop
jigsaw,1,0,,Decoupeerzaag (Electric Jigsaw),Woodshop
Desoldeerbout,1,0,,Desoldeerbout,Electronics
drillpress-wood,1,0,,Drill press / boorkolom,Woodshop
'''

class Command(BaseCommand):
    help = 'Does some magical work'

    def handle(self, *args, **options):

        for line in sys.stdin:
           line = line.strip()
           print(line)
           name, i, p, pt, desc,location = line.split(',')

           if name=='name' or name.startswith('#'):
               continue

           permit = None
           loc = None
           machine = None

           if pt:
               permit,wasCreated = PermitType.objects.get_or_create(name=pt)
               permit.description = 'Permit to use ' + pt
               permit.changeReason = "Added during bulk import."
               permit.save()

           if location:
               loc,wasCreated = Location.objects.get_or_create(name=location)
               loc.changeReason = "Added during bulk import."
               loc.save()

           machine,wasCreated = Machine.objects.get_or_create(name=name)
           machine.description = desc

           if location:
                  machine.location = loc 
           if int(i)>0:
                  machine.requires_instruction = True
           else:
                  machine.requires_instruction = False
           if pt:
                  machine.requires_form = True
                  machine.requres_permit = pt
           machine.changeReason = "Added during bulk import."
           machine.save()
