from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

import sys, os
import datetime


class Command(BaseCommand):
    help = "Show all balances"

    def handle(self, *args, **options):
        rc = 0

        print("# Member,Balance,lastchange")

        for balance in PettycashBalanceCache.objects.all():
            dt = "None"
            if balance.last:
                dt = balance.last.date

            print("%s,%s,%s" % (balance.owner, balance.balance, dt))

        sys.exit(rc)
