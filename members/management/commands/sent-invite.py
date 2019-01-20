from django.core.management.base import BaseCommand, CommandError

from simple_history.models import HistoricalRecords
from members.models import User
from members.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.conf import settings
from django.core.mail import EmailMessage

import sys,os
''' 
Sent invites; to just one user, or all users
in the system,
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
    help = 'Sent invite to email adddress(es) provided - or read them from stdin.'

    def add_arguments(self, parser):
        parser.add_argument('email', nargs='*', type=str)

        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            help='Sent a poll to -everyone-. Ignores anything specified on stdin/arguments',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            help='Also reset/block the current account. So any (old) password will not work any longer.',
       )

    def handle(self, *args, **options):
        rc = 0
        if options['all']:
            if options['email']:
                print("The option --all cannot be used with additional emails specified as arguments.", file=sys.stderr)
                rc = 1
            else:
                for user in User.objects.all():
                   rc |= not reset_password(user.email, options['reset'])
        elif options['email']:
            for email in options['email']:
                rc |= not reset_password(email, options['reset'])
        else:
            for email in sys.stdin:
                rc |= not reset_password(email, options['reset'])

        sys.exit(rc)
