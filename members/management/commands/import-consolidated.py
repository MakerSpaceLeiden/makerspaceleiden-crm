from django.core.management.base import BaseCommand, CommandError

from members.models import PermitType
from simple_history.models import HistoricalRecords
from members.models import User
from members.models import PermitType,Entitlement,Tag,User
from acl.models import Machine,Instruction,Location
from memberbox.models import Memberbox
from storage.models import Storage

import sys,os

class Command(BaseCommand):
    help = 'Does some magical work'

    def handle(self, *args, **options):
        """ Do your work here """
        # self.stdout.write('There are {} things!'.format(User.objects.count()))
        user0 = None
        cup = 0
        while True:
           email = sys.stdin.readline().strip()
           if email == '':
              break
           tags = sys.stdin.readline().strip()
           name = sys.stdin.readline().strip()
           what = sys.stdin.readline().strip()
           phone = sys.stdin.readline().strip()
           member = None

           try:
               member = User.objects.get(email=email)
               if not user0:
                   user0 = member

           except User.DoesNotExist:
               member = User()
               member.email = email
               if ' ' in name:
                 member.first_name = name.split(' ',1)[0]
                 member.last_name = name.split(' ',1)[1] 
               else:
                 member.first_name = name
                 member.last_name = ''
               if len(what.split(' ')) > 1:
                  member.form_on_file = True
               member.save()
               if not user0:
                   user0 = member
               self.stdout.write('Imported {} <{}>'.format(name,email))
           except Exception as e:
               raise e
           for w in what.split(' '):
                # loc = Location(name = 'At the usual spot')
               try:
                 permit = PermitType.objects.get(name = w)
               except PermitType.DoesNotExist:
                 permit = PermitType()
                 permit.name = w
                 permit.description = 'The ' + w + ' permit'
                 permit.save()
               except Exception as e:
                 raise e
               try:
                 machine = Machine.objects.get(name = w)
               except Machine.DoesNotExist:
                 machine = Machine()
                 machine.name = w
                 machine.description = 'The ' + w + ' machine'
                 # machine.location = loc 
                 machine.requires_form = True 
                 machine.requires_instruction = True
                 machine.requires_permit = permit
                 self.stdout.write('Imported {}'.format(what))
                 # loc.save()
                 machine.save()
               except Exception as e:
                 raise e
               try:
                 entit = Entitlement.objects.get(permit = permit, holder = member, issuer = user0)
               except Entitlement.DoesNotExist:
                 entit = Entitlement(permit = permit, holder = member, issuer = user0)
                 entit.save()
               except Exception as e:
                 raise e

           col = cup % 6
           row = int(cup/6) % 6
           k = int(cup/36)
           cup += 1
           l = 'random spot '+str(cup)
           if k == 0:
                   l = 'L'+str(col)+str(row)
           if k == 1:
                   l = 'R'+str(col)+str(row)
           try:
                  box = Memberbox.objects.get(location = l)
           except Memberbox.DoesNotExist:
                  box = Memberbox()
                  box.owner = member
                  box.location = l
                  box.description = 'The nice box of '+str(member)
                  box.save()
           except Exception as e:
                 raise e
