from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q

from ufo.models import Ufo

from ufo.utils import emailUfoInfo

import sys, os
import datetime


class Command(BaseCommand):
    help = "Sent reminders for UFOs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--save",
            dest="save",
            type=str,
            help="Save the message as rfc822 blobs rather than sending. Useful as we sort out dkim on the server. Pass the output directo ry as an argument",
        )
        parser.add_argument(
            "--to",
            dest="to",
            type=str,
            help="Sent the message to a different addres (default is "
            + settings.MAILINGLIST
            + ").",
        )

    def handle(self, *args, **options):
        rc = 0
        DAYS = 12
        deadline = datetime.date.today() + datetime.timedelta(days=DAYS)

        if options["save"]:
            settings.EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
            settings.EMAIL_FILE_PATH = options["save"]

        dests = [settings.MAILINGLIST]

        if options["to"]:
            dests = [options["to"]]

        # Items that are still identified and will go 'can be disposed' in  days, or
        # that are going out completely.
        #
        postDeadline = (
            Ufo.objects.filter(Q(state="UNK"))
            .filter((Q(deadline__lt=deadline)))
            .filter(Q(dispose_by_date__gte=deadline))
        )
        postDisposeline = Ufo.objects.filter(
            (Q(state="UNK") & Q(dispose_by_date__lt=deadline)) | Q(state="DEL")
        )

        items = {}
        for item in postDeadline:
            items[item.id] = item
        for item in postDisposeline:
            items[item.id] = item

        context = {
            "postDeadline": postDeadline,
            "postDisposeline": postDisposeline,
        }
        if items:
            emailUfoInfo(
                list(items.values()), "email_notification_reminder", dests, context
            )

        sys.exit(rc)
