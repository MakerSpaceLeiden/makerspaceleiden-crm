import sys

from django.core.management.base import BaseCommand

from pettycash.models import PettycashBalanceCache


class Command(BaseCommand):
    help = "Show all balances"

    def handle(self, *args, **options):
        rc = 0

        print("# Member,Balance,lastchange")

        for balance in PettycashBalanceCache.objects.all():
            dt = "None"
            if balance.last:
                dt = balance.last.date

            print("%s,%s,%s" % (balance.owner, balance.balance, dt))

        sys.exit(rc)
