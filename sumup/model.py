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
        "ERROR": "Internal error or unknown state reported by Sumup",
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
    client_transaction_id = models.CharField(max_length=48, blank=True, null=True)
    transaction_id = models.CharField(max_length=48, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True, help_text="Date of sumup callback")

    debug_note = models.CharField(max_length=512,blank=True, null=True, 
             help_text="Additional information on SumUP state when applicable")

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
        if state != 'PREPARED':
            raise Exception(f"Sumup transact: State of {pk} is already {state}, cannot submit.")

        state = 'PENDING'
        save() # we need to get our PK

	description = f"MSL-f{pk}-f{member.pk}-f{terminal.pk}, f{member} deposit"

        body=CreateReaderCheckoutBody(
            description=description
	    return_url='https://weser.webweaving.org/cgi-bin/sumup?src=6512766745',
	    tip_rates = [],
	    total_amount=CreateReaderCheckoutAmount(currency ='EUR', minor_unit=2, value='1000')
        ))

        # Update the transaction state
        client_transaction_id = checkout.data.client_transaction_id
        state = 'SUBMITTED'
        date = datetime.now()
        save()
