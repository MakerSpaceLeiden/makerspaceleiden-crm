from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

import sys, os
import datetime

from moneyed import Money, EUR


class Command(BaseCommand):
    help = "Show all balances"

    def handle(self, *args, **options):
        rc = 0

        total = Money(0, EUR)
        for balance in PettycashBalanceCache.objects.all():
            if balance.last:
                total += balance.last.amount

        print("Balance across all accounts: %s" % (total))

        sys.exit(rc)
