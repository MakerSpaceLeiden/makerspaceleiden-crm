import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from rich import print as printr
from sumup import APIError, Sumup
from sumup.transactions.resource import GetTransactionParams


class Command(BaseCommand):
    help = "List all transactions"

    def add_arguments(self, parser):
        parser.add_argument(
            "-r", "--raw", action="store_true", help="Show raw (as opposed to TSV)"
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

        transactions = client.transactions.list(settings.SUMUP_MERCHANT)
        if options["raw"]:
            printr(transactions)
            sys.exit(rc)

        print("#status    	amount		type	card      	description")
        for tx in transactions.items:
            print(
                f"{tx.status:10}	{tx.amount} {tx.currency}	{tx.type}	{tx.card_type:12}	{tx.product_summary}"
            )
            if True:
                try:
                    printr(
                        client.transactions.get(
                            settings.SUMUP_MERCHANT, GetTransactionParams(id=tx.id)
                        )
                    )
                except APIError:
                    pass  # print(f"Error: {e.status} - {e.body}")
        sys.exit(rc)
