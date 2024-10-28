import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from mail import emailPlain

from acl.models import Entitlement


class Command(BaseCommand):
    help = "Sent reminders on dangling permissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--save",
            dest="save",
            type=str,
            help="Save the message as rfc822 blobs rather than sending. Useful as we sort out dkim on the server. Pass the output directory as an argument",
        )
        parser.add_argument(
            "--to",
            dest="to",
            type=str,
            help="Sent the message to a different addres (default is the user)",
        )

    def handle(self, *args, **options):
        rc = 0

        if options["save"]:
            settings.EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
            settings.EMAIL_FILE_PATH = options["save"]

        for e in (
            Entitlement.objects.all()
            .filter(active=False)
            .filter(holder__is_active=True)
        ):
            dests = [e.owner.email]
            if options["to"]:
                dests = [options["to"]]

            context = {
                "user": e.owner,
                "instructor": e.issuer,
                "machine": e.permit,
                "waiver": e.owner.form_on_file,
                "trustees": e.active,
                "trustees_email": settings.TRUSTEES,
            }
            emailPlain(
                "email_acl_processupdate.txt",
                subject="[ACL@MSL] Reminder/status of machine permissions",
                toinform=dests,
                context=context,
            )

        sys.exit(rc)
