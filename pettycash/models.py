import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from djmoney.models.fields import MoneyField
from djmoney.models.validators import MinMoneyValidator
from moneyed import EUR, Money
from simple_history.models import HistoricalRecords
from stdimage.models import StdImageField

from acl.models import Location
from makerspaceleiden.mail import emailPlain
from makerspaceleiden.utils import upload_to_pattern
from members.models import User, none_user
from terminal.models import Terminal

logger = logging.getLogger(__name__)


def pettycash_admin_emails():
    return list(
        User.objects.all()
        .filter(groups__name=settings.PETTYCASH_ADMIN_GROUP)
        .values_list("email", flat=True)
    )


class PettycashSku(models.Model):
    name = models.CharField(max_length=300, blank=False, null=True)
    description = models.CharField(max_length=300, blank=False, null=True)
    amount = MoneyField(
        max_digits=8,
        decimal_places=2,
        default_currency="EUR",
        null=True,
    )

    history = HistoricalRecords()

    def __str__(self):
        return "%s (%s)" % (self.name, self.amount)


class PettycashStation(models.Model):
    terminal = models.ForeignKey(
        Terminal,
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
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="pettycash_cache",
    )

    balance = MoneyField(
        max_digits=8, decimal_places=2, null=True, default_currency="EUR"
    )

    lasttxdate = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date of most recent balance changing transaction (excluding any technical/system ones)",
    )

    history = HistoricalRecords()

    def url(self):
        return settings.BASE + self.path()

    def path(self):
        return reverse("balances", kwargs={"pk": self.id})

    def save(self):
        if not self.owner:
            self.owner = none_user()

        return super(PettycashBalanceCache, self).save()

    def __str__(self):
        return "{} {}".format(self.balance, self.owner)


def adjust_balance_cache(last, dst, amount, comment=None, isreal=True):
    try:
        balance = PettycashBalanceCache.objects.get(owner=dst)
        balance.balance += amount

    except ObjectDoesNotExist:
        balance = PettycashBalanceCache(owner=dst, balance=Money(0, EUR))
        for tx in PettycashTransaction.objects.all().filter(Q(dst=dst)):
            balance.balance += tx.amount
        for tx in PettycashTransaction.objects.all().filter(Q(src=dst)):
            balance.balance -= tx.amount

        logger.info(
            "Warning - creating petty cache entry for dst=%s - filled with %s"
            % (dst, balance.balance)
        )

    if isreal:
        balance.lasttxdate = timezone.now()

    if comment is None:
        comment = "Change {} : {}".format(amount, dst)
    balance._change_reason = comment[:99]
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

    # There is a bug/limitation in Django's admin interface:
    # https://docs.djangoproject.com/en/dev/ref/contrib/admin/actions/
    #
    # so we do below from an signal rather than 'normal' delete(), and
    # register this as a callback/signal on 'pre_delete' of any
    # trnsaction.
    #
    def delete_callback(self, *args, **kwargs):
        try:
            # Essentially roll the transaction back from the cache.
            if self.src != self.dst:
                adjust_balance_cache(
                    self, self.src, self.amount, comment="Deleted tx {}".format(self)
                )
                adjust_balance_cache(
                    self, self.dst, -self.amount, comment="Deleted tx {}".format(self)
                )
        except Exception as e:
            logger.error("Transaction cache failure on update post delete: %s" % (e))

    def refund_booking(self, reason="Refund"):
        """
        Refund a booking by doing a new 'reverse' booking, this way all amounts stay positive
        """
        new_transaction = PettycashTransaction()
        new_transaction.src = self.dst
        new_transaction.dst = self.src
        new_transaction.amount = self.amount
        new_transaction.description = "refund %s (%d)" % (self.description, self.pk)
        new_transaction._change_reason = reason
        new_transaction.save()

    def save(self, *args, **kwargs):
        bypass = False

        max_val = settings.MAX_PAY_CRM.amount
        if kwargs is not None:
            if "bypass" in kwargs:
                bypass = kwargs["bypass"]
                del kwargs["bypass"]

            if "is_privileged" in kwargs:
                max_val = settings.MAX_PAY_TRUSTEE.amount
                del kwargs["is_privileged"]

        if self.pk:
            if not bypass:
                raise ValidationError(
                    "you may not edit an existing Transaction - instead create a new one"
                )
            logger.info("Bypass used on save of %s" % self)

        if not self.date:
            self.date = timezone.now()

        if not self.src:
            self.src = none_user()
        if not self.dst:
            self.dst = none_user()

        if self.amount < Money(0, EUR):
            if not bypass:
                raise ValidationError("Blocked negative transaction.")
            logger.info("Bypass for negative transaction used on save of %s" % self)

        if self.amount > Money(max_val, EUR):
            if not bypass:
                raise ValidationError("Amount too high.")
            logger.info("Bypass on max limites used on save of %s" % self)

        if self._change_reason:
            self._change_reason = self._change_reason[:99]

        rc = super(PettycashTransaction, self).save(*args, **kwargs)
        try:
            if self.src != self.dst:
                adjust_balance_cache(self, self.dst, self.amount)
                adjust_balance_cache(self, self.src, -self.amount)
            else:
                logger.critical("ODD: transfer from %s to %s of %s".format())
        except Exception as e:
            logger.error("Transaction cache failure: %s" % (e))

        return rc


class PettycashReimbursementRequest(models.Model):
    src = models.ForeignKey(
        User,
        help_text="Party that pays (usually the %s)" % (settings.POT_LABEL),
        on_delete=models.CASCADE,
        related_name="isReimbursedBy",
        default=settings.POT_ID,
    )

    dst = models.ForeignKey(
        User,
        help_text="Person to reemburse (usually you, yourself)",
        on_delete=models.CASCADE,
        related_name="isReimbursedTo",
    )

    date = models.DateField(help_text="Date of expense", default=timezone.now)

    submitted = models.DateTimeField(
        help_text="Date the request was submitted",
        default=timezone.now,
    )

    amount = MoneyField(
        max_digits=8,
        decimal_places=2,
        default_currency="EUR",
    )

    viaTheBank = models.BooleanField(
        default=False,
        help_text="Check this box if you want to be paid via a IBAN/SEPA transfer; otherwise the amount will be credited to your Makerspace petty cash acount",
    )
    isPayout = models.BooleanField(default=False, help_text="Internal hidden field")

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

    def __str__(self):
        return "%s Reimburse request %s %s (from %s) for: %s bank:%s" % (
            self.date,
            self.amount,
            self.dst,
            self.src,
            self.description,
            self.viaTheBank,
        )


class PettycashImportRecord(models.Model):
    date = models.DateField(help_text="Date of last import", default=timezone.now)
    by = models.ForeignKey(
        User,
        help_text="Person that did this import",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )


# See above note/comment near delete_callback(). We need
# to do this _pre_ -- as we want to record the name of
# the user leaving and use the transaction itself. And
# cannot do this once things are deleted.
#
@receiver(pre_delete, sender=PettycashTransaction)
def pre_delete_tx_callback(sender, instance, using, **kwargs):
    tx = instance
    tx.delete_callback(using, kwargs)


@receiver(pre_delete, sender=User)
def pre_delete_user_callback(sender, instance, using, **kwargs):
    # Run through all the current transactions of the user;
    # sum them up; and move the balance to former participant
    # account. In effect - we keep a PL in this account.
    #
    user = instance
    name = str(user)

    amount = Money(0.0, EUR)
    for tx in PettycashTransaction.objects.all().filter(Q(dst=user)):
        amount += tx.amount
    for tx in PettycashTransaction.objects.all().filter(Q(src=user)):
        amount -= tx.amount

    msg = "donating"
    f = User.objects.get(id=settings.NONE_ID)
    t = User.objects.get(id=settings.POT_ID)

    if amount < Money(0, EUR):
        msg = "with a debt"
        t, f = f, t
        amount = -amount

    if amount == Money(0, EUR):
        msg = "with no debt or money in the pettycash"
    else:
        tx = PettycashTransaction(
            src=f,
            dst=t,
            amount=amount,
            description=f"Deleted participant {name} left {msg}",
        )
        tx._change_reason = "Participant was deleted"
        tx.save()

    emailPlain(
        "email_payout_leave.txt",
        toinform=pettycash_admin_emails(),
        context={
            "user": name,
            "amount": amount,
            "msg": msg,
        },
    )
