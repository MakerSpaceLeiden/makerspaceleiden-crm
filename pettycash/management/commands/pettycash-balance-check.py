import sys

from django.core.management.base import BaseCommand

from pettycash.models import PettycashBalanceCache


class Command(BaseCommand):
    help = "Show all balances"

    def handle(self, *args, **options):
        rc = 0

        total = 0

        for e in PettycashBalanceCache.objects.all():
            if e.balance.amount:
                total += e.balance.amount

        print(f"Balance across all accounts: {total}")

        sys.exit(rc)
