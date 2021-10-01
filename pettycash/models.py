from django.conf import settings
from simple_history.models import HistoricalRecords
from djmoney.models.fields import MoneyField
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import ModelChoiceField
from django.db.models import Q

from django.db.models.signals import pre_delete, pre_save

from django.db import models
from members.models import User

from django.utils import timezone
from datetime import datetime, timedelta
import uuid
import os
import re
from moneyed import Money, EUR

import logging
logger = logging.getLogger(__name__)

class PettycashBalanceCache(models.Model):
     owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null = True)

     balance = MoneyField(max_digits=10, decimal_places=2, null=True, default_currency='EUR')
     last = models.ForeignKey('PettycashTransaction', on_delete=models.SET_DEFAULT, null=True, blank=True, default = None)

     history = HistoricalRecords()

     def url(self):
       return settings.BASE + self.path()

     def path(self):
       return reverse('balances', kwargs = { 'pk' :  self.id })

def adjust_balance_cache(last, dst,amount):
     try:
           balance = PettycashBalanceCache.objects.get(owner=dst)
     except ObjectDoesNotExist as e:
           print("Warning - creating for dst=%s" % (dst))

           balance =  PettycashBalanceCache(owner=dst,balance=Money(0,EUR))
           for tx in PettycashTransaction.objects.all().filter(Q(dst=dst)):
              balance.balance += tx.amount

     balance.balance += amount
     balance.last = last
     balance.save()

class PettycashTransaction(models.Model):
     dst = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'isReceivedBy', blank=True, null = True)
     src = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'isSentBy',  blank=True, null = True)

     date =  models.DateTimeField(blank=True, null = True)

     amount = MoneyField(max_digits=10, decimal_places=2, null=True, default_currency='EUR')
     description = models.CharField(max_length=300, blank=True, null=True)

     history = HistoricalRecords()

     def url(self):
       return settings.BASE + self.path()

     def path(self):
       return reverse('transactions', kwargs = { 'pk' :  self.id })

     def __str__(self):
         if self.dst == self.src:
            return "@%s BALANCE %s" % (self.date, self.amount)
         return "@%s %s->%s '%s' %s" % (self.date, self.src, self.dst, self.description, self.amount)

     def delete(self, * args, ** kwargs):
         rc = super(PettycashTransaction,self).delete(*args, **kwargs)
         try:
             adjust_balance_cache(self, self.src, self.amount)
             adjust_balance_cache(self, self.dst, -self.amount)
         except Exception as e:
             print("Transaction cache failure on delete: %s" % (e))

         return rc

     def save(self, * args, ** kwargs):
         if self.pk:
            raise ValidationError("you may not edit an existing Transaction - instead create a new one")

         if not self.date:
             self.date = datetime.now(tz=timezone.utc)
         
         rc = super(PettycashTransaction,self).save(*args, **kwargs)
         try:
             adjust_balance_cache(self, self.src, -self.amount)
             adjust_balance_cache(self, self.dst, self.amount)
         except Exception as e:
             print("Transaction cache failure: %s" % (e))

         return rc
