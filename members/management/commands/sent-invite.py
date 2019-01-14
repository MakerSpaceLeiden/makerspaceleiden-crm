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
def reset_password(email, 
        from_email=settings.FROM_EMAIL, 
        template='members/email_invite.txt'):
    try:
        user = User.objects.get(email=email)
    except Exception as e:
        print("No user with email address <{}> found.".format(email), file=sys.stderr)
        return False

    form = PasswordResetForm({'email': email })

    if not form.is_valid():
        raise Exception("Eh - internal issues")
    if form.save(from_email=from_email, email_template_name=template):
        print("Email to {} sent.".format(email))
    else:
        print("Sending to  <{}> failed.".format(email), file=sys.stderr)
        return False

    return True

class Command(BaseCommand):
    help = 'Sent invite to email adddress(es) provided - or read them from stdin.'

    def add_arguments(self, parser):
        parser.add_argument('email', nargs='*', type=str)

    def handle(self, *args, **options):
        if options['email']:
            for email in options['email']:
                if not reset_password(email):
                    sys.exit(1)
        else:
            for email in sys.stdin:
                if not reset_password(email):
                    sys.exit(1)
