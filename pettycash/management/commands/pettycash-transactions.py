from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

import sys,os
import datetime

class Command(BaseCommand):
    help = 'Show all balances'

    def handle(self, *args, **options):
        rc = 0

        print("# Src,Dst,date,desc,amount")

        for tx in PettycashTransaction.objects.all():
           print("%s,%s,%s,%s,%s" % (tx.src,tx.dst,tx.date,tx.description,tx.amount))
           
        sys.exit(rc)
