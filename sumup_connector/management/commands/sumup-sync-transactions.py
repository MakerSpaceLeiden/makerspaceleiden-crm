import sys
from django.conf import settings
from rich import print as printr

from django.core.management.base import BaseCommand

from sumup_connector.models import Checkout
from sumup_connector.sumupapi import SumupAPI, SumupError


class Command(BaseCommand):
    help = "List all transactions"

    def add_arguments(self , parser):
       parser.add_argument('-u', '--update', action="store_true",
            help='Actually update the data to match')

    def handle(self, *args, **options):
        rc = 0

        if not hasattr(settings, 'SUMUP_MERCHANT'):
             print("SumUp Merchant code not configured. Aborting.", file=sys.stderr)
             sys.exit(-1)
        if not hasattr(settings, 'SUMUP_API_KEY'):
             print("SumUp API key not configured. Aborting.", file=sys.stderr)
             sys.exit(-2)

        api = SumupAPI(settings.SUMUP_MERCHANT, settings.SUMUP_API_KEY)
        txs = api.list_transactions()


        n = len(txs)
        print(f"Aantal hits: {n}")

        tids = []
        ctids = []
        for tx in txs:
            tids.append(tx['transaction_id'])
            ctids.append(tx['client_transaction_id'])

            try:
                 c = Checkout.objects.get(client_transaction_id = tx['client_transaction_id'])
            except Exception as e:
                 print(f"Transaction {tx['transaction_id']} missing")
                 continue;

            if tx['transaction_id'] != c.transaction_id:
                 if  c.transaction_id == None:
                      print(f"Missing transaction_id (known sumup bug)")
                      c.transaction_id = tx['transaction_id']
                      if options['update']:
                             c = c.save()
                 else:
                      print(f"Transaction f{tx['transaction_id']}, mismatching with {c.pk}: {c.transaction_id}")

            if (tx['status'] == 'SUCCESSFUL' and c.state != 'SUCCESSFUL'):
                 print(f"Transaction f{tx['transaction_id']}, #{c.pk}: crm:{c.state} != sumup:{tx['status']} -- missing deposit")
            elif (tx['status'] != 'SUCCESSFUL' and c.state == 'SUCCESSFUL'):
                 print(f"Transaction f{tx['transaction_id']}, #{c.pk}: crm:{c.state} != sumup:{tx['status']} -- deposit needs to be rolled back")
            elif tx['status'] == 'FAILED' and c.state == 'CANCELLED':
                 pass
            elif tx['status'] !=  c.state:
                 print(f"Transaction f{tx['transaction_id']}, #{c.pk}: crm:{c.state} != sumup:{tx['status']}")

        for c in Checkout.objects.filter(state = 'SUCCESSFUL'):
            if c.transaction_id is not None and c.transaction_id not in tids:
                 print(f"#{c.pk}: transaction id {c.transaction_id} not at sumup; but paid out")
            if c.client_transaction_id is not None and c.client_transaction_id not in ctids:
                 print(f"#{c.pk}: client transaction id {c.client_transaction_id} not at sumup; but paid out")
            
        sys.exit(rc)
