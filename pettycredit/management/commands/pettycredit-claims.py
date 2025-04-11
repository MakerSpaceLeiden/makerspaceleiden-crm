import sys

from django.core.management.base import BaseCommand

from pettycredit.models import PettycreditClaim, PettycreditClaimChange


class Command(BaseCommand):
    help = "Show all claims"

    def handle(self, *args, **options):
        rc = 0
        for c in PettycreditClaim.objects.all():
            print(f"- {c.src}->{c.dst} - {c.date}")
            print(f"  {c.description}")
            for l in PettycreditClaimChange.objects.filter(claim_id=c.pk):
                print(f"  - {l.description} - {l.date}")
            status = "** PENDING"
            if c.settled:
                status = "settled"
            print(f"  Amount: {c.amount} {status}")

        sys.exit(rc)
