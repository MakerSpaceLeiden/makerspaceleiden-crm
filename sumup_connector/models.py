from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from moneyed import EUR, Money
from djmoney.models.fields import MoneyField
from djmoney.models.validators import MinMoneyValidator

from simple_history.models import HistoricalRecords

from makerspaceleiden.mail import emailPlain
from members.models import User

from terminal.models import Terminal
from pettycash.models import PettycashTransaction
from pettycash.views import alertOwnersToChange

from django.contrib.sites.shortcuts import get_current_site

from datetime import datetime
import logging
import secrets
import hashlib
import json

from sumup import Sumup, APIError
from sumup.checkouts.resource import CreateCheckoutBody
from sumup.readers.types import CreateReaderCheckoutAmount
from sumup.readers.resource import CreateReaderBody, CreateReaderCheckoutBody


logger = logging.getLogger(__name__)

def gen_hash(pk,time):
    val = settings.SUMUP_NONCE + '-' + str(pk) + '-' + str(int(time))
    sha = hashlib.sha256(val.encode('utf-8')).hexdigest()
    return sha[0:16]

class Checkout(models.Model):
    STATES = (
        ( "PREPARED", "Prepared but not yet submitted to sumit" ),
        ( "SUBMITTED", "Submitted to sumup; no callback yet" ),
        ( "SUCCESSFUL", "Sumup reported the transaction as successful" ),
        ( "CANCELLED", "Sumup reported the transaction as cancelled (usually by the end user" ),
        ( "FAILED", "Sumup reported transaction failed" ),
        ( "PENDING", "Sumup reported the transaction pending" ),
        ( "ERROR", "Internal error or unknown state reported by Sumup" ),
    )

    member = models.ForeignKey(
        User,
        help_text="Participants that pays into the pot",
        on_delete=models.SET_NULL,
        related_name="isPaidBy",
        blank=True,
        null=True,
    )
    date = models.DateTimeField(blank=True, null=True, default=timezone.now,
          help_text="Date of start of the transaction")

    amount = MoneyField(
        max_digits=8,
        decimal_places=2,
        null=True,
        default_currency="EUR",
        validators=[MinMoneyValidator(0)],
        help_text = 'Amount shown on the display of the Sumup terminal',
    )
    terminal = models.ForeignKey(
        Terminal,
        related_name="paidOnStation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text = 'Station/terminal used for this payment',
    )
    client_transaction_id = models.CharField(max_length=48, blank=True, null=True,
	help_text = 'Client transaction ID as reported by SumUp during initial request to activate SOLO')
    transaction_id = models.CharField(max_length=48, blank=True, null=True,
	help_text = 'Transaction reported back from Sumup after the payment completed on the SOLO terminal')
    transaction_date = models.DateTimeField(blank=True, null=True, help_text="Date of sumup callback")

    settled_tx = models.ForeignKey(
        PettycashTransaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text = "Actual settlement into the participants account (if any)",
    )

    debug_note = models.JSONField(max_length=512,blank=True, null=True, 
             help_text="Additional information on SumUP state when applicable")

    state = models.CharField(
        max_length=16, choices=STATES, default="PREPARED", blank=True, null=True
    )

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.amount}, {self.state} {self.member}"

    def url(self):
        return settings.BASE + self.path()

    def path(self):
        return reverse("checkouts", kwargs={"pk": self.id})

    # Submit to sumup
    #
    # For now in the model; should move this out to
    # a controller if we start collecting too much logic
    #
    def transact(self):
        if self.pk != None and self.state != 'PREPARED':
            raise Exception(f"Sumup transact: State of {self.pk} is already {state}, cannot submit.")

        self.state = 'PENDING'
        self._change_reason = 'Initial creation with no data; to get a pk reference for SumUP'
        self.save() # we need to get our PK

        self.description = f"MSL-{self.pk}-{self.member.pk}-{self.terminal.pk}, {self.member}, sumup deposit"
        self.date = timezone.now()
        try:
            url = self.signed_callback_url()
            logger.info(url)
            body = CreateReaderCheckoutBody(
                description=self.description,
                return_url=url,
                tip_rates = [],
                total_amount=CreateReaderCheckoutAmount(currency ='EUR', minor_unit=2, value=100 * self.amount.amount)
            )
            client = Sumup(api_key=settings.SUMUP_API_KEY)
            
            checkout = client.readers.create_checkout(
                     merchant_code = settings.SUMUP_MERCHANT,
	             id = settings.SUMUP_READER, 
                     body = body,
            )
            self.debug_note = checkout.model_dump_json()
            self.client_transaction_id = checkout.data.client_transaction_id
            self.state = 'SUBMITTED'

        except APIError as e:
            self.state = 'ERROR'
            if e.status == 422:
                 self.state = 'FAILED'
            logger.error(f"transact({self.pk}) failed: {e} --  {e.status} {e.body}")
            self.debug_note = e.body

        self._change_reason = 'Submitted to Sumup'
        self.save()

    def deposit(self, transaction_id, timestamp):
        # Transact first; so we leave an error if the transaction fails.
        #
        tx = PettycashTransaction(
             src=User.objects.get(id=settings.POT_ID),
             dst=self.member,
             amount=self.amount,
             description=f"Sumup deposit at {self.terminal.name}, {transaction_id}"
        )
        tx._change_reason = f"Sumpup; f{transaction_id}"
        tx.save()
 
        fee = Money(self.amount.amount * settings.SUMUP_FEE_PERCENTAGE / 100)
        actual_amount = Money(self.amount.amount / (1 + settings.SUMUP_FEE_PERCENTAGE / 100))

        txf = PettycashTransaction(
             src=self.member,
             dst=User.objects.get(id=settings.POT_ID),
             amount=fee,
             description=f"Transaction fee {transaction_id}, #{tx.pk}"
        )
        txf._change_reason = f"Sumpup fee; f{transaction_id}"
        txf.save()

        self.state = 'SUCCESSFUL'
        self.settled_tx = tx

        self.transaction_id = transaction_id
        self.transaction_date = timestamp
        self._change_reason = f"{transaction_id}/{self.pk} Complete; references for the deposit: {tx.pk} and fee: {txf.pk}"

        self.save()

        alertOwnersToChange(tx, userThatMadeTheChange = self.member, template = 'sumup/email_deposit.txt', {
             'fee': , fee, 
             'actual_amount': actual_amount 
        }

    def signed_callback_url(self):
        url = ''.join(['https://', 
                #get_current_site(None).domain, 
                settings.SUMUP_HACK,
		reverse('sumup-v1-callback', kwargs = {
			'sumup_pk': self.pk,
			'timeint': int(self.date.timestamp()),
			'hash': gen_hash(self.pk,self.date.timestamp())
	        })])
        return url
