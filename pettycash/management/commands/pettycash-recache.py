from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from pettycash.models import PettycashBalanceCache, PettycashTransaction
from members.models import User

from moneyed import Money, EUR

import sys,os
import datetime

class Command(BaseCommand):
    help = 'Recache all balances'

    def handle(self, *args, **options):
        rc = 0

        for user in User.objects.all():
           balance =  PettycashBalanceCache(owner=user, balance=Money(0,EUR))
           old_balance = Money(0,EUR)

           try:
              balance = PettycashBalanceCache.objects.get(owner=user)
              old_balance = balance.balance
           except ObjectDoesNotExist as e:
              pass

           balance.balance = Money(0,EUR)

           trns = []
           try:
              trns =  PettycashTransaction.objects.all().filter(Q(dst=user) | Q(src=user))
              for tx in trns:
                  if tx.dst == user:
                      balance.balance += tx.amount
                  else:
                      balance.balance -= tx.amount
           except ObjectDoesNotExist as e:
              pass

           old_balance = old_balance - balance.balance
           err = ''
           if old_balance != Money(0,EUR):
                err = ' (error: %s)' % old_balance

           print("%s: %s%s", % (user, balance.balance, err))

           balance.save()
           
        sys.exit(rc)
