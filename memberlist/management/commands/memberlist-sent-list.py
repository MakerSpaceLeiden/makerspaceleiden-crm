import sys
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from makerspaceleiden.mail import emailPlain
from members.models import User


def sendEmail(
    toinform, template="monthly-participants-email.txt", forreal=True, context={}
):
    context["date"] = datetime.now(tz=timezone.utc).date()
    context["base"] = settings.BASE

    for e in [toinform] if isinstance(toinform, str) else toinform:
        emailPlain(
            template,
            toinform=[e],
            context=context,
            forreal=forreal,
        )


class Command(BaseCommand):
    help = "Sent overview of all active participants"

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to",
            type=str,
            help="Sent the message to a different addres (default is to %s)"
            % (settings.MAILINGLIST),
        )

        parser.add_argument(
            "--direct",
            dest="direct",
            action="store_true",
            help="Sent the message directly to the users, rather than to the mailing list.",
        )

        parser.add_argument(
            "--all",
            dest="all",
            action="store_true",
            help="Also include inactive people.",
        )

        parser.add_argument(
            "--save",
            dest="save",
            type=str,
            help="Save the message as rfc822 blobs rather than sending. Useful as we sort out dkim on the server. Pass the output directory as an argument",
        )

        parser.add_argument(
            "--dry-run",
            dest="dryrun",
            action="store_true",
            help="Do a dry run; do not actually sent",
        )

    def handle(self, *args, **options):
        _ = int(options["verbosity"])
        rc = 0

        if options["save"]:
            settings.EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
            settings.EMAIL_FILE_PATH = options["save"]

        users = User.objects.all()
        if not options["all"]:
            users = users.filter(is_active=True)

        dest = settings.MAILINGLIST
        if options["direct"]:
            dest = users.values_list("email", flat=True)
        if options["to"]:
            dest = options["to"]

        sendEmail(
            dest,
            forreal=(not options["dryrun"]),
            context={
                "participants": users,
                "num": users.count,
            },
        )

        sys.exit(rc)
