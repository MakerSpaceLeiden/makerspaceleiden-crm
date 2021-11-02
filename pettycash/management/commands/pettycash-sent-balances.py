from django.core.management.base import BaseCommand, CommandError

from django.template.loader import render_to_string, get_template
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q

from pettycash.models import PettycashTransaction, PettycashBalanceCache
from makerspaceleiden.mail import emailPlain

import sys, os, pwd

from datetime import datetime, timedelta
from django.utils import timezone
from moneyed import Money, EUR


def sendEmail(balances, toinform, template="balance-overview-email.txt"):
    for e in [toinform] if isinstance(toinform, str) else toinform:
        emailPlain(
            template,
            toinform=[e],
            context={
                "balances": balances,
                "date": datetime.now(tz=timezone.utc),
                "base": settings.BASE,
            },
        )


class Command(BaseCommand):
    help = "Sent balance overview of everyone"

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
            help="Also include people with a 0 balance.",
        )

        parser.add_argument(
            "--days",
            dest="days",
            action="store",
            default=100,
            type=int,
            help="Ignore people who did not do a transaction in this many days (default is 100)",
        )

        parser.add_argument(
            "--save",
            dest="save",
            type=str,
            help="Save the message as rfc822 blobs rather than sending. Useful as we sort out dkim on the server. Pass the output directory as an argument",
        )

    def handle(self, *args, **options):
        verbosity = int(options["verbosity"])
        cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=options["days"])
        rc = 0

        if options["save"]:
            settings.EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
            settings.EMAIL_FILE_PATH = options["save"]

        balances = PettycashBalanceCache.objects.order_by("balance")
        if not options["all"]:
            balances = balances.filter(
                Q(balance__gt=Money(0, EUR)) | Q(balance__lt=Money(0, EUR))
            ).filter(Q(last__date__gt=cutoff_date))

        dest = settings.MAILINGLIST
        if options["to"]:
            dest = options["to"]

        if options["direct"]:
            dest = balances.values_list("owner__email", flat=True)

        if balances.count():
            sendEmail(balances, dest)
        else:
            print("No balances sent - none done since %s" % cutoff_date)

        sys.exit(rc)
