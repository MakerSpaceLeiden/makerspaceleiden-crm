from django.core.management.base import BaseCommand, CommandError

from django.template.loader import render_to_string, get_template
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q

from pettycash.models import PettycashTransaction, PettycashBalanceCache

import sys,os
from datetime import datetime, timedelta
from django.utils import timezone
from moneyed import Money, EUR

def sendEmail(balances, to, template = 'balance-overview-email.txt'):
    subject = "[makerbot] Account balances for this month"

    context = {
           'balances': balances,
           'date': datetime.now(tz=timezone.utc),
           'base': settings.BASE,
    }
    message = render_to_string(template, context)
    EmailMessage(subject, message, to=[to], from_email=settings.DEFAULT_FROM_EMAIL).send()

class Command(BaseCommand):
    help = 'Sent balance overview of everyone'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            dest='to', type = str,
            help='Sent the message to a different addres (default is to %s)' % (settings.MAILINGLIST)
        )

        parser.add_argument(
            '--save',
            dest='save', type = str, 
            help='Save the message as rfc822 blobs rather than sending. Useful as we sort out dkim on the server. Pass the output directory as an argument',
        )

    def handle(self, *args, **options):
        rc = 0

        if options['save']:
            settings.EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
            settings.EMAIL_FILE_PATH = options['save']

        dest = settings.MAILINGLIST
        if options['to']:
           dest = options['to']

        balances = PettycashBalanceCache.objects.all().order_by('balance')
        sendEmail(balances, dest)

        sys.exit(rc)
