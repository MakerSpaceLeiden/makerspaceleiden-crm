import logging
from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone
from djmoney.models.fields import MoneyField
from djmoney.models.validators import MinMoneyValidator
from moneyed import EUR, Money

from members.models import User
from pettycash.models import PettycashTransaction

logger = logging.getLogger(__name__)


def claim_experiry_default():
    now = timezone.now()
    return now + timedelta(hours=settings.CLAIM_EXPIRY_HOURS)


class PettycreditClaim(models.Model):
    dst = models.ForeignKey(
        User,
        help_text="Whom to pay the money to",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    src = models.ForeignKey(
        User,
        related_name="isDeptor",
        help_text="Whom paid you",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    settled = models.BooleanField(
        default=False,
        help_text="Wether or not the claim has been settled already",
    )
    settled_tx = models.ForeignKey(
        PettycashTransaction,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    date = models.DateTimeField(
        default=timezone.now,
        help_text="Date of the claim",
    )
    end_date = models.DateTimeField(
        default=claim_experiry_default,
        help_text="Expiry date of the claim; when it gets auto charged/rolled up",
    )
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

    def __str__(self):
        return "@%s %s (claim) '%s' %s" % (
            self.date,
            self.src,
            self.description,
            self.amount,
        )

    def updateclaim(self, desc=None, amount=None, hours=0):
        if desc is None:
            desc = f"{self.description} (update)"
        with transaction.atomic():
            PettycreditClaimChange(description=desc, claim_id=self).save()
            if amount is None:
                self.amount = amount
            if hours > 0:
                self.end_date = timezone.now() + timedelta(hours=float(hours))
            self.save()

    def settle(self, desc=None, amount=None):
        if desc is None:
            desc = self.description
        if amount is None:
            amount = self.amount
        with transaction.atomic():
            PettycreditClaimChange(
                description=f"{desc} (final settling)", claim_id=self
            ).save()

            if amount != Money(0, EUR):
                tx = PettycashTransaction(
                    src=self.src,
                    dst=self.dst,
                    amount=amount,
                    description=desc,
                )
                tx.save()
                self.settled_tx = tx

            self.amount = amount
            self.settled = True
            super().save()


class PettycreditClaimChange(models.Model):
    claim_id = models.ForeignKey(PettycreditClaim, on_delete=models.CASCADE)
    date = models.DateTimeField(
        default=timezone.now,
        help_text="Date of the claim change",
    )
    description = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Reason for the change",
    )


@receiver(pre_delete, sender=User)
def pre_delete_user_callback(sender, instance, using, **kwargs):
    # Run through all the current outstanding claims of the user;
    # sum them up; and move the balance to former participant
    # account. In effect - we keep a PL in this account.
    #
    user = instance
    name = str(user)

    amount = Money(0.0, EUR)
    for tx in PettycreditClaim.objects.all().filter(Q(src=user)):
        amount += tx.amount
        # We do not bother with setting the settled flag; as
        # these records are about to be deleted.

    if amount != Money(0, EUR):
        tx = PettycashTransaction(
            src=User.objects.get(id=settings.POT_ID),
            dst=User.objects.get(id=settings.NONE_ID),
            amount=amount,
            description=f"Deleted participant {name} left with claims still open",
        )
        tx._change_reason = "Participant was deleted; claims rolled up"
        tx.save()
