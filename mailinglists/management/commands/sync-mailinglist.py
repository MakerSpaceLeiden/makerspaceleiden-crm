from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from django.conf import settings

from members.models import User
from mailinglists.models import Mailinglist, Subscription, MailmanAccount, MailmanService

import sys,os

class Command(BaseCommand):
    help = 'Sync roster from remote service; and create/sync it with the local one.'

    def add_arguments(self, parser):

        parser.add_argument( '--all', dest='all', action='store_true', help='List all mailing lists; rather than just one',)
        parser.add_argument( '--dryrun', dest='dry', action='store_true', help='Show what would be done; but do not do it',)
        parser.add_argument( '--url', dest='url', type = str, help='Admin URL',)
        parser.add_argument( '--password', dest='password', type = str, help='Admin Password',)

        # parser.add_argument('dir', choices = ['list2crm', 'crm2list','compare'])
        parser.add_argument('listname', nargs='*')

    def handle(self, *args, **options):
        if options['all']:
           lists = Mailinglist.objects.all()
        else:
           lists = [Mailinglist.objects.get(name = name) for name in options['listname']]

        if len(lists) == 0:
            raise CommandError('Noting to do.')

        # We do not use the default option of parser - as to not reveal settings needlessly.
        if 'password' in options:
             password = options['password']

        if 'url' in options:
             url = options['url']

        dryrun = options['dry']

        service = MailmanService(password, url)
        for mlist in lists:
           print(f'# {mlist.name}: {mlist.description}')

            #system = []
           # for s in  Subscription.objects.all().filter(mailinglist__name = mlist):
           #    system.append(s.member.email)
           # known = User.objects.all().values_list('email', flat=True)

           users = User.objects.filter(is_active = True)
           known = []
           e2u = {}
           for u in users:
              known.append(u.email)
              e2u[ u.email ] = u

           # system = Subscription.objects.all().values_list('member__email', flat=True)
           subs = Subscription.objects.all()
           system = []
           e2s = {}
           for s in subs:
              system.append(s.member.email)
              e2s[ s.member.email ] = s

           account = MailmanAccount(service, mlist)
           roster = account.roster()

           for email in sorted(list(set(roster)|set(system)|set(known))):
                if email in roster and email in system:
                   sub = e2s[ email ]

                   print(f'{email}\n\tboth on roster and on server.')

                   v = account.delivery(email)
                   if sub.active != v:
                       print(f"\tACTION: update active flag to {v}")
                       if not dryrun:
                          sub.active = v
                          sub.save()
                   else:
                       print(f'\tactive/delivery flag in sync.')

                   v = account.digest(email)
                   if sub.digest != v:
                       print(f"\tACTION: update digest flag to {v}")
                       if not dryrun:
                          sub.digest = v
                          sub.save()
                   else:
                       print(f'\tdigest flag in sync.')
 
                elif email in known and email in system:
                   print(f'{email}\n \tmissing on roster - but we think it should be subscribed')
                   print(f"\tACTION: Subscribing on server")
                   if dryrun:
                       continue
                   
                   s = Subscription.objects.get(mailinglist == mlist, member.email == email)
                   s.subscribe()
                   # s.changeReason("Sync Subscribed during command sync")
                   s.save()

                elif email in known and email in roster:
                   print(f'{email}\n \ton the roster - but not recorded as subscribed.')
                   print(f"\tACTION: record as subscribed")
                   if dryrun:
                       continue
                   s = Subscription(member = e2u[email], mailinglist = mlist, digest = False, active = False)
                   s.save()

                elif email in known:
                   print(f'{email}\n \tmissing on roster - and not recorded as subscribed.')
                   print(f"\tACTION: Subscribing onto the roster AND recoring as subscribed")
                   if dryrun:
                       continue
                   s = Subscription(member = e2u[email], mailinglist = mlist, digest = False, active = False)
                   s.subscribe()
                   # s.changeReason("Subscribed during command sync and added to the mailing list server")
                   s.save()

                elif email in roster:
                   print(f'{email}\n \tnot in the crm, but on the roster -- not removed (IGNORED).')
                else:
                   raise Exception("bug")
 
        sys.exit(0)
