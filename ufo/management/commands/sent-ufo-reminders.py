from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q

from members.models import User
from ufo.models import Ufo

from ufo.utils import emailUfoInfo

import sys,os
import datetime

class Command(BaseCommand):
    help = 'Sent reminders for UFOs.'

    def handle(self, *args, **options):
        rc = 0
        DAYS=7
        deadline = datetime.date.today() + datetime.timedelta(days=DAYS)

        # Items that are still identified and will go 'can be disposed' in  days, or
        # that are going out completely.
        #
        postDeadline = Ufo.objects.filter(Q(state = 'UNK')).filter((Q(deadline__lt=deadline))).filter(Q(dispose_by_date__gte=deadline))
        postDisposeline = Ufo.objects.filter(Q(state = 'UNK') | Q(state = 'DEL')).filter(Q(dispose_by_date__lt=deadline))

        items = {}
        for item in postDeadline:
             items[ item.id ] = item
        for item in postDisposeline:
             items[ item.id ] = item
        context = {
            'postDeadline': postDeadline,
            'postDisposeline': postDisposeline,
        }
        emailUfoInfo(items.values(), 'email_notification_reminder', [ settings.MAILINGLIST ], context )

        sys.exit(rc)
