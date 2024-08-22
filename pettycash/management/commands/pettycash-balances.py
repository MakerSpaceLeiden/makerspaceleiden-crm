import sys

from django.core.management.base import BaseCommand

from pettycash.models import PettycashBalanceCache


class Command(BaseCommand):
    help = "Show all balances"

    def handle(self, *args, **options):
        rc = 0

        #        print("# Member,Balance,lastchange")
        print("# Member,Balance")

        for balance in PettycashBalanceCache.objects.all():
            dt = "Never"
            if balance.lasttxdate:
                dt = balance.lasttxdate

            print("%s,%s,%s" % (balance.owner, balance.balance, dt))

        sys.exit(rc)
