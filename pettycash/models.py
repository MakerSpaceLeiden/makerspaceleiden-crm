from django.conf import settings
from simple_history.models import HistoricalRecords
from djmoney.models.fields import MoneyField
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

from django.db.models.signals import pre_delete, pre_save

from django.db import models
from members.models import User

import datetime
import uuid
import os
import re
from moneyed import Money, EUR

import logging
logger = logging.getLogger(__name__)

class PettycashBalanceCache(models.Model):
     owner = models.ForeignKey(User, on_delete=models.CASCADE)
     balance = MoneyField(max_digits=10, decimal_places=2, null=True, default_currency='EUR')
     last = models.ForeignKey('PettycashTransaction', on_delete=models.CASCADE,null=True)

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
           balance =  PettycashBalanceCache.objects(owner=dst,balance=Money(0,EUR))
           for tx in PettycashTransaction.objects.all().filter(Q(owner=dst)):
              balance.balance += tx.amount

     balance.balance += amount
     balance.last = last
     balance.save()

class PettycashTransaction(models.Model):
     dst = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'isReceivedBy')
     src = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'isSentBy',  blank=True, null = True)

     date =  models.DateField(blank=True, null = True)

     amount = MoneyField(max_digits=10, decimal_places=2, null=True, default_currency='EUR')
     description = models.CharField(max_length=300, blank=True, null=True)

     history = HistoricalRecords()

     def url(self):
       return settings.BASE + self.path()

     def path(self):
       return reverse('transactions', kwargs = { 'pk' :  self.id })

     def __str__(self):
         return self.description

     def save(self, * args, ** kwargs):
         if self.pk:
            raise ValidationError("you may not edit an existing Transaction - instead create a new one")

         self.date =  datetime.date.today()
         
         rc = super(PettycashTransaction,self).save(*args, **kwargs)
         try:
             adjust_balance_cache(self, self.src, -self.amount)
             adjust_balance_cache(self, self.dst, self.amount)
         except Exception as e:
             print("Transaction cache failure: %s" % (e))

         return rc