from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q

from pettycash.models import Pettycash

from pettycash.utils import emailPettycashInfo

import sys,os
import datetime

class Command(BaseCommand):
    help = 'Sent balances and stuff..

    def add_arguments(self, parser):
         parser.add_argument(
            '--to',
            dest='to', type = str,
            help='Sent the message to a different addres (default is to just the owners knwon email)',
         )

    def handle(self, *args, **options):
        rc = 0

        dests = [ settings.MAILINGLIST ]
        if options['to']:
            dests = [ options['to'] ]

        #   emailPettycashInfo(list(items.values()), 'email_notification_reminder', dests, context )

        sys.exit(rc)
