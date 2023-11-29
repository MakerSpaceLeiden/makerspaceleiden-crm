import sys

from django.core.management.base import BaseCommand
from moneyed import EUR, Money

from pettycash.models import PettycashBalanceCache


class Command(BaseCommand):
    help = "Show all balances"

    def handle(self, *args, **options):
        rc = 0

        total = Money(0, EUR)
        for balance in PettycashBalanceCache.objects.all():
            if balance.last:
                total += balance.last.amount

        print("Balance across all accounts: %s" % (total))

        sys.exit(rc)
