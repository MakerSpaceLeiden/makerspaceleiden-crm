import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from rich import print as printr
from sumup import APIError, Sumup
from sumup.readers.resource import CreateReaderBody


class Command(BaseCommand):
    help = "Pair a new reader"

    def add_arguments(self, parser):
        parser.add_argument(
            "paircode",
            type=str,
            help="reader pairing code as shown on SumUp solo display, typically 8-ish uppercase alphanums",
        )
        parser.add_argument("name", type=str, help="humand readable name")

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

        try:
            res = client.readers.create(
                settings.SUMUP_MERCHANT,
                CreateReaderBody(
                    pairing_code=options["paircode"], name=options["name"], meta={}
                ),
            )
            printr(res)
        except APIError as e:
            print(f"Failed to pair reader: {e.status} - {e.body}")

        sys.exit(rc)
