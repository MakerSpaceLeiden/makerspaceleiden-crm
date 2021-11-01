from django.conf import settings
from simple_history.models import HistoricalRecords
from djmoney.models.fields import MoneyField
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms.models import ModelChoiceField
from django.db.models import Q
from django.utils import timezone
from djmoney.models.validators import MaxMoneyValidator, MinMoneyValidator
from stdimage.models import StdImageField
from stdimage.validators import MinSizeValidator, MaxSizeValidator

from django.db.models.signals import pre_delete, pre_save

from acl.models import Location

from django.db import models
from members.models import User

from makerspaceleiden.mail import emailPlain
from makerspaceleiden.utils import upload_to_pattern

from django.utils import timezone
from datetime import datetime, timedelta
import uuid
import os
import re
import base64
import hashlib
import binascii
import datetime

from moneyed import Money, EUR

import logging

logger = logging.getLogger(__name__)

import base64
import hashlib


def pemToSHA256Fingerprint(pem):
    pem = pem[27:-25]
    der = base64.b64decode(pem.encode("ascii"))
    return hashlib.sha256(der).hexdigest()


def hexsha2pin(sha256_hex_a, sha256_hex_b):
    a = binascii.unhexlify(sha256_hex_a)
    b = binascii.unhexlify(sha256_hex_b)
    if (len(a) != 32) or (len(b) != 32):
        raise NameError("Not a SHA256")
    fp = hashlib.sha256(a + b).hexdigest()
    return fp[:6].upper()


class PettycashSku(models.Model):
    name = models.CharField(max_length=300, blank=True, null=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    amount = MoneyField(
        max_digits=8, decimal_places=2, null=True, default_currency="EUR"
    )
    history = HistoricalRecords()

    def __str__(self):
        return "%s (%s)" % (self.name, self.amount)


class PettycashTerminal(models.Model):
    name = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Name, initially as reported by the firmware. Potentially not unique!",
    )
    fingerprint = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="SHA256 fingerprint of the client certificate.",
    )
    nonce = models.CharField(
        max_length=64, blank=True, null=True, help_text="256 bit nonce (as HEX)"
    )
    date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Time and date the device was last seen",
        auto_now_add=True,
    )
    accepted = models.BooleanField(
        default=False,
        help_text="Wether an administrator has checked the fingerprint against the display on the device and accepted it.",
    )
    history = HistoricalRecords()

    def __str__(self):
        return "%s@%s %s...%s" % (
            self.name,
            self.date.strftime("%Y/%m/%d %H:%M"),
            self.fingerprint[:3],
            self.fingerprint[-3:],
        )

    def save(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(
            minutes=settings.PETTYCASH_TERMS_MINS_CUTOFF
        )

        # Drop anything that is too old; and only keep the most recent up to
        # a cap -- feeble attempt at foiling obvious DOS. Mainly as the tags
        # can be as short as 32 bits and we did not want to also add a shared
        # scecret in the Arduino code. As these easily get committed to github
        # by accident.
        stale = (
            PettycashTerminal.objects.all().filter(Q(accepted=False)).order_by("date")
        )
        if len(stale) > settings.PETTYCASH_TERMS_MAX_UNKNOWN:
            lst = (
                User.objects.all()
                .filter(groups__name=settings.PETTYCASH_ADMIN_GROUP)
                .values_list("email", flat=True)
            )
            emailPlain(
                "pettycash-dos-warn.txt",
                toinform=lst,
                context={"base": settings.BASE, "settings": settings, "stale": stale},
            )
            logger.info("DOS mail set about too many terminals in waiting.")
        todel = set()
        for s in stale.filter(Q(date__lt=cutoff)):
            todel.add(s)
        for s in stale[settings.PETTYCASH_TERMS_MIN_UNKNOWN :]:
            todel.add(s)
        for s in todel:
            s.delete()

        return super(PettycashTerminal, self).save(*args, **kwargs)


class PettycashStation(models.Model):
    terminal = models.ForeignKey(
        PettycashTerminal,
        related_name="station",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    description = models.CharField(max_length=300, blank=True, null=True)
    location = models.ForeignKey(
        Location, related_name="terminalIsLocated", on_delete=models.SET_NULL, null=True
    )
    default_sku = models.ForeignKey(
        PettycashSku,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="defaultSku",
        help_text="Default SKU (or the only one) at boot time and reverted to after 60 seconds",
    )
    available_skus = models.ManyToManyField(
        PettycashSku,
        blank=True,
        related_name="availableSku",
        help_text="SKUs avaialble at this terminal, when supported (or empty)",
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.description


class PettycashBalanceCache(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    balance = MoneyField(
        max_digits=8, decimal_places=2, null=True, default_currency="EUR"
    )
    last = models.ForeignKey(
        "PettycashTransaction",
        on_delete=models.SET_DEFAULT,
        null=True,
        blank=True,
        default=None,
        help_text="Last transaction that changed the balance",
    )

    history = HistoricalRecords()

    def url(self):
        return settings.BASE + self.path()

    def path(self):
        return reverse("balances", kwargs={"pk": self.id})


def adjust_balance_cache(last, dst, amount):
    try:
        balance = PettycashBalanceCache.objects.get(owner=dst)
    except ObjectDoesNotExist as e:
        logger.info("Warning - creating for dst=%s" % (dst))

        balance = PettycashBalanceCache(owner=dst, balance=Money(0, EUR))
        for tx in PettycashTransaction.objects.all().filter(Q(dst=dst)):
            # Exclude the current transaction we are working with
            if tx.id is not last.id:
                balance.balance += tx.amount

    balance.balance += amount
    balance.last = last
    balance.save()


class PettycashTransaction(models.Model):
    dst = models.ForeignKey(
        User,
        help_text="Whom to pay the money to",
        on_delete=models.CASCADE,
        related_name="isReceivedBy",
        blank=True,
        null=True,
    )
    src = models.ForeignKey(
        User,
        help_text="Whom paid you",
        on_delete=models.CASCADE,
        related_name="isSentBy",
        blank=True,
        null=True,
    )

    date = models.DateTimeField(blank=True, null=True, help_text="Date of transaction")

    amount = MoneyField(
        max_digits=8,
        decimal_places=2,
        null=True,
        default_currency="EUR",
        validators=[MinMoneyValidator(0)],
    )
    description = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Description / omschrijving van waarvoor deze betaling is",
    )

    history = HistoricalRecords()

    def url(self):
        return settings.BASE + self.path()

    def path(self):
        return reverse("transactions", kwargs={"pk": self.id})

    def __str__(self):
        if self.dst == self.src:
            return "@%s BALANCE %s" % (self.date, self.amount)
        return "@%s %s->%s '%s' %s" % (
            self.date,
            self.src,
            self.dst,
            self.description,
            self.amount,
        )

    def delete(self, *args, **kwargs):
        rc = super(PettycashTransaction, self).delete(*args, **kwargs)
        try:
            adjust_balance_cache(self, self.src, self.amount)
            adjust_balance_cache(self, self.dst, -self.amount)
        except Exception as e:
            logger.error("Transaction cache failure on delete: %s" % (e))

        return rc

    def refund_booking(self):
        """
        Refund a booking by doing a new 'reverse' booking, this way all amounts stay positive
        """
        new_transaction = PettycashTransaction()
        new_transaction.src = self.dst
        new_transaction.dst = self.src
        new_transaction.amount = self.amount
        new_transaction.description = "refund %s (%d)" % (self.description, self.pk)
        new_transaction.save()

    def save(self, *args, **kwargs):
        bypass = False

        if kwargs is not None and "bypass" in kwargs:
            bypass = kwargs["bypass"]
            del kwargs["bypass"]
        if self.pk:
            if not bypass:
                raise ValidationError(
                    "you may not edit an existing Transaction - instead create a new one"
                )
            logger.info("Bypass used on save of %s" % self)

        if not self.date:
            self.date = datetime.now(tz=timezone.utc)

        if self.amount < Money(0, EUR):
            if not bypas:
                raise ValidationError("Blocked negative transaction.")
            logger.info("Bypass for negative transaction used on save of %s" % self)

        rc = super(PettycashTransaction, self).save(*args, **kwargs)
        try:
            adjust_balance_cache(self, self.src, -self.amount)
            adjust_balance_cache(self, self.dst, self.amount)
        except Exception as e:
            logger.error("Transaction cache failure: %s" % (e))

        return rc


class PettycashReimbursementRequest(models.Model):
    dst = models.ForeignKey(
        User, 
        help_text="Person to reemburse (usually you, yourself)",
        on_delete=models.CASCADE,
        related_name="isReimbursedTo",
    )

    date = models.DateTimeField(help_text="Date of expense", default=datetime.date.today)

    submitted = models.DateTimeField(
        help_text="Date the request was submitted", default=datetime.date.today,
    )

    amount = MoneyField(
        max_digits=8,
        decimal_places=2,
        null=True,
        default_currency="EUR",
        validators=[
            MinMoneyValidator(0),
            MaxMoneyValidator(settings.MAX_PAY_REIMBURSE.amount),
        ],
        help_text="This system will only accept reimbursement up to %s. Above that; contact the trustees directly (%s)"
        % (settings.MAX_PAY_REIMBURSE.amount, settings.TRUSTEES),
    )

    viaTheBank = models.BooleanField(
        default=False,
        help_text="Check this box if you want to be paid via a IBAN/SEPA transfer; otherwise the amount will be credited to your Makerspace petty cash acount",
    )

    description = models.CharField(
        max_length=300,
        help_text="Description / omschrijving van waarvoor deze betaling is",
    )

    scan = StdImageField(
        upload_to=upload_to_pattern,
        delete_orphans=True,
        variations=settings.IMG_VARIATIONS,
        validators=settings.IMG_VALIDATORS,
        blank=True,
        null=True,
        help_text="Scan, photo or similar of the receipt",
    )
    history = HistoricalRecords()
