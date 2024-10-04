import datetime
import sys

from django.core.management.base import BaseCommand
from django.db.models import Q

from pettycredit.models import PettycreditClaim


class Command(BaseCommand):
    help = "Process any pending claims"

    def handle(self, *args, **options):
        cutoff = datetime.date.today() + datetime.timedelta(days=0)
        rc = 0

        for c in PettycreditClaim.objects.filter(Q(end_date__lt=cutoff)):
            c.settle("Forced settlement due to claim expiring", c.amount)

        sys.exit(rc)
