import sys

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Q
from moneyed import EUR, Money

from members.models import User
from pettycash.models import PettycashBalanceCache, PettycashTransaction


def pettycash_recache(verbosity=0, dryrun=0):
    rc = 0
    total = Money(0, EUR)
    for user in User.objects.all():
        balance = PettycashBalanceCache(owner=user, balance=Money(0, EUR))
        old_balance = Money(0, EUR)
        act = "cache fault/correction"
        try:
            balance = PettycashBalanceCache.objects.get(owner=user)
            old_balance = balance.balance
        except ObjectDoesNotExist:
            act = "initial creation"
            pass

        balance.balance = Money(0, EUR)

        trns = []
        try:
            trns = PettycashTransaction.objects.all().filter(Q(dst=user) | Q(src=user))
            for tx in trns:
                if tx.dst == user:
                    balance.balance += tx.amount
                    total += tx.amount
                else:
                    balance.balance -= tx.amount
                    total -= tx.amount
        except ObjectDoesNotExist:
            pass

        old_balance = old_balance - balance.balance
        err = ""
        if old_balance != Money(0, EUR) or act == "initial creation":
            err = " (%s: %s)" % (act, old_balance)
            if not dryrun:
                balance._change_reason = act
                balance.save()
        if err != "" and act != "initial creation":
            rc = -1
        if (err != "" and act != "initial creation") or verbosity > 1:
            print("%s: %s%s" % (user, balance.balance, err))

    if total != Money(0, EUR):
        rc = -2

    if total != Money(0, EUR) or verbosity > 1:
        print("Total %s" % (total))
    return rc


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
        rc = pettycash_recache(int(options["verbosity"]), options["dryrun"])
        sys.exit(rc)
