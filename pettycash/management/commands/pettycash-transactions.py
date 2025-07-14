import sys
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from pettycash.models import PettycashTransaction


class Command(BaseCommand):
    help = "Show all balances"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            dest="days",
            type=int,
            help="Number of dates to show, default is everything available",
        )

    def handle(self, *args, **options):
        rc = 0

        print("# Src,Dst,date,desc,amount,euros")
        txs = PettycashTransaction.objects.all()
        if options["days"]:
            cutoff_date = datetime.now(tz=timezone.utc) - timedelta(
                days=options["days"]
            )
            txs = txs.filter(date__gte=cutoff_date)

        for tx in txs:
            print(
                '"%s","%s","%s","%s","%s",%.02f'
                % (tx.src, tx.dst, tx.date, tx.description, tx.amount, tx.amount.amount)
            )

        sys.exit(rc)
