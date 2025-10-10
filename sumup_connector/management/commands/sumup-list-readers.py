import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from rich import print as printr
from sumup import Sumup


class Command(BaseCommand):
    help = "List all readers"

    def handle(self, *args, **options):
        rc = 0

        if not hasattr(settings, "SUMUP_MERCHANT"):
            # if settings.SUMUP_MERCHANT in locals():
            print("SumUp Merchant code not configured. Aborting.", file=sys.stderr)
            sys.exit(-1)
        if not hasattr(settings, "SUMUP_API_KEY"):
            print("SumUp API key not configured. Aborting.", file=sys.stderr)
            sys.exit(-2)

        client = Sumup(api_key=settings.SUMUP_API_KEY)
        merchant = client.merchant.get()

        if merchant.merchant_profile.merchant_code != settings.SUMUP_MERCHANT:
            print("SumUp merchant code appears malformed. Aborting.", file=sys.stderr)
            sys.exit(-3)

        readers = client.readers.list(settings.SUMUP_MERCHANT)
        printr(readers)

        sys.exit(rc)
