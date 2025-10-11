import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from rich import print as printr
from sumup import APIError, Sumup


class Command(BaseCommand):
    help = "Delete a reader"

    def add_arguments(self, parser):
        parser.add_argument(
            "rdr_code", type=str, help="Specify reader rdr_xxx code to delete"
        )

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
            print(args)
            res = client.readers.delete_reader(
                settings.SUMUP_MERCHANT, options["rdr_code"]
            )
            printr(res)
        except APIError as e:
            print(f"Failed to delete reader: {e.status} - {e.body}")

        sys.exit(rc)
