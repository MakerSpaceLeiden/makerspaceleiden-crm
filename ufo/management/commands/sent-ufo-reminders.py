from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q

from members.models import User
from ufo.models import Ufo

from ufo.utils import emailUfoInfo

import sys,os
import datetime

''' 
Sent reminders for any UFOs that will soo
change state.
'''
def reset_password(email, reset = False,
        from_email=settings.DEFAULT_FROM_EMAIL, 
        template='members/email_invite.txt',
        subject_template='members/email_invite_subject.txt',
        ):
    try:
        user = User.objects.get(email=email)
    except Exception as e:
        print("No user with email address <{}> found.".format(email), file=sys.stderr)
        return False

    if reset:
        user.set_unusable_password()
        user.changeReason = "Locked it from the sent-invite command."
        user.save()

    form = PasswordResetForm({'email': email })

    if not form.is_valid():
        raise Exception("Eh - internal issues")

    try:
        form.save(from_email=from_email, email_template_name=template, subject_template_name=subject_template)
        print("{} - Email sent.".format(email))
    except Exception as e:
        print("Sending to  <{}> failed: {}".format(email,e), file=sys.stderr)
        return False

    return True

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
        emailUfoInfo(items.values(), 'email_notification_reminder', None, [ settings.MAILINGLIST ], context )

        sys.exit(rc)
