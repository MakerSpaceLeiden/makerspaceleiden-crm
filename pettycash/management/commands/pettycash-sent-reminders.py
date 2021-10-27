from django.core.management.base import BaseCommand, CommandError

from django.template.loader import render_to_string, get_template
from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.utils import timezone

from pettycash.models import PettycashTransaction, PettycashBalanceCache
from makerspaceleiden.mail import emailPlain

import sys, os
from datetime import datetime
from moneyed import Money, EUR


def sendEmail(transactions, balance, user, toinform, template="balance-email.txt"):
    gs = False
    topup = 0
    if balance.balance > Money(0, EUR):
        gs = True
    else:
        topup = (
            int((-float(balance.balance.amount) + settings.PETTYCASH_TOPUP) / 5 + 0.5)
            * 5
        )
    return emailPlain(
        template,
        toinform=toinform,
        context={
            "base": settings.BASE,
            "balance": balance,
            "date": datetime.now(tz=timezone.utc),
            "transactions": transactions,
            "goodstanding": gs,
            "topup": topup,
            "user": user,
        },
    )


class Command(BaseCommand):
    help = "Sent balances and stuff.."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            dest="to",
            type=str,
            help="Sent the message to a different addres (default is to just the owners knwon email)",
        )

        parser.add_argument(
            "--save",
            dest="save",
            type=str,
            help="Save the message as rfc822 blobs rather than sending. Useful as we sort out dkim on the server. Pass the output directory as an argument",
        )

    def handle(self, *args, **options):
        rc = 0

        if options["save"]:
            settings.EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
            settings.EMAIL_FILE_PATH = options["save"]

        for balance in PettycashBalanceCache.objects.all():
            user = balance.owner

            if user.id == settings.POT_ID:
                continue

            if balance.balance == 0:
                continue

            transactions = (
                PettycashTransaction.objects.all()
                .filter(Q(src=user) | Q(dst=user))
                .order_by("date")
            )
            if transactions.count() == 0:
                continue

            dests = [user.email]
            if options["to"]:
                dests = [options["to"]]

            sendEmail(transactions, balance, user, dests)

        sys.exit(rc)
