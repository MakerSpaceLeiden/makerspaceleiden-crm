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

class Checkout(models.Model):
    STATES = { 
        "PREPARED": "Prepared but not yet submitted to sumit",
        "SUBMITTED": "Submitted to sumup; no callback yet",
        "SUCCESSFUL": "Sumup reported the transaction as successful",
        "CANCELLED": "Sumup reported the transaction as cancelled (usually by the end user",
        "FAILED": "Sumup reported transaction failed",
        "PENDING": "Sumup reported the transaction pending",
        "ERROR": "Internal error",
    }

    member = models.ForeignKey(
        User,
        help_text="Participants that pays into the pot",
        on_delete=models.SET_NULL,
        related_name="isPaidBy",
        blank=True,
        null=True,
    )
    date = models.DateTimeField(blank=True, null=True, help_text="Date of start of the transaction")
    amount = MoneyField(
        max_digits=8,
        decimal_places=2,
        null=True,
        default_currency="EUR",
        validators=[MinMoneyValidator(0)],
    )
    terminal = models.ForeignKey(
        Terminal,
        related_name="station",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    sumup_tx = models.CharField(max_length=300, blank=True, null=True)

    state = models.CharField(
        max_length=4, choices=STATES, default="PREPARED", blank=True, null=True
    )

    history = HistoricalRecords()

    def url(self):
        return settings.BASE + self.path()

    def path(self):
        return reverse("checkouts", kwargs={"pk": self.id})

    # Submit to sumup
    #
    # For now in the model; should move this out to 
    # a controller if we start collecting too much logic
    #
    def transact(self, terminal):
        save() # we need to get our PK
	description = f"MSL-f{pk}-f{member.pk}-f{terminal.pk}, f{member} deposit"

