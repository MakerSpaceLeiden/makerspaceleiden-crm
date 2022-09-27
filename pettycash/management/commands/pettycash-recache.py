from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

from moneyed import Money, EUR

import sys, os
import datetime


class Command(BaseCommand):
    help = "Recache all balances"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dryrun",
            help="Do a dry-run; do not actually save.",
        )

    def handle(self, *args, **options):
        rc = 0
        verbosity = int(options["verbosity"])

        total = Money(0, EUR)
        for user in User.objects.all():
            balance = PettycashBalanceCache(owner=user, balance=Money(0, EUR))
            old_balance = Money(0, EUR)
            act = "correction"
            try:
                balance = PettycashBalanceCache.objects.get(owner=user)
                old_balance = balance.balance
            except ObjectDoesNotExist as e:
                act = "initial creation"
                pass

            balance.balance = Money(0, EUR)

            trns = []
            try:
                trns = PettycashTransaction.objects.all().filter(
                    Q(dst=user) | Q(src=user)
                )
                for tx in trns:
                    if tx.dst == user:
                        balance.balance += tx.amount
                        total += tx.amount
                    else:
                        balance.balance -= tx.amount
                        total -= tx.amount
            except ObjectDoesNotExist as e:
                pass

            old_balance = old_balance - balance.balance
            err = ""
            if old_balance != Money(0, EUR) or act == "initial creation":
                err = " (%s: %s)" % (act, old_balance)
                if not options["dryrun"]:
                    balance._change_reason = act
                    balance.save()
            if (err != "" and act != "initial creation") or verbosity > 1:
                print("%s: %s%s" % (user, balance.balance, err))

        if total != Money(0, EUR) or verbosity > 1:
            print("Total %s" % (total))
        sys.exit(rc)
