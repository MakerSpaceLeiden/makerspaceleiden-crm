import sys

from django.core.management.base import BaseCommand

from pettycash.models import PettycashTransaction


class Command(BaseCommand):
    help = "Show all balances"

    def handle(self, *args, **options):
        rc = 0

        print("# Src,Dst,date,desc,amount")

        for tx in PettycashTransaction.objects.all():
            print(
                "%s,%s,%s,%s,%s" % (tx.src, tx.dst, tx.date, tx.description, tx.amount)
            )

        sys.exit(rc)
