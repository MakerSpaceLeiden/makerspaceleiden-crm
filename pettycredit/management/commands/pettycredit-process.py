import datetime
import sys

from django.core.management.base import BaseCommand
from django.db.models import Q

from pettycredit.models import PettycreditClaim


class Command(BaseCommand):
    help = "Process any pending claims"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            dest="days",
            action="store",
            default=0,
            type=int,
            help="Run this as-if so many days into the future, useful for testing or a purge",
        )

    def handle(self, *args, **options):
        cutoff = datetime.date.today() + datetime.timedelta(days=options["days"])
        rc = 0

        for c in PettycreditClaim.objects.filter(Q(end_date__lt=cutoff)):
            c.description = f"{c.description} (settlement due to claim expiring)"
            c.settle("Settlement due to claim expiring", c.amount)

        sys.exit(rc)
