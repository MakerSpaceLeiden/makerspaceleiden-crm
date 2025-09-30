from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse

from moneyed import EUR, Money
from simple_history.models import HistoricalRecords

from makerspaceleiden.mail import emailPlain
from members.models import User

from terminal.models import Terminal
from pettycash.models import ettycashTransaction

from django.contrib.sites.shortcuts import get_current_site

logger = logging.getLogger(__name__)

NONCE = secrets.token_bytes(48)
if 'sumup_nonce' in settings:
    NONCE = settings.sumup_nonce

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
        start_time= datetime.now()
        try:
            body = CreateReaderCheckoutBody(
                description=description,
                return_url=signed_callback_url(),
                tip_rates = [],
                total_amount=CreateReaderCheckoutAmount(currency ='EUR', minor_unit=2, value='1000')
            )
            client_transaction_id = checkout.data.client_transaction_id
            state = 'SUBMITTED'

        except APIError as e:
            state = 'ERROR'
            if e.status == 422:
                 state = 'FAILED'
            debug_note = _ecleanse(e) 
        save()

    def deposit(self, data):
        # Transact first; so we leave an error if the transaction fails.
        #
        tx = PettycashTransaction(
             src=User.objects.get(id=settings.POT_ID),
             dst=checkout.member,
             amount=checkout.amount,
             description=f"Sumup deposit at f{terminal},  f{checkout.transaction_id}"
        )
        tx._change_reason = f"Sumpup; f{data}"
        tx.save()

        checkout.status = 'SUCCESSFUL'
        checkout.save()

        alertOwnersToChange(tx, template = 'sumup/email_deposit.txt')
    
    def gen_hash(self, pk, time):
        return hashlib.sha256(NONCE + str(pk) + str(time))[0:15]

    def signed_callback_url(self, time):
        return '',join(['https://', get_current_site(NONE).domain, 
		reverse('sumup-v1-callback', self.pk, time, gen_hash(self.pk. time))])

    def _cleanse(e):
        #            {"errors":{"detail":"Unprocessable Entity"}}
        if 'errors' in e:
            if 'detail' in e.errors:
                return f"{e.errors.body}"
            return f"{e.errors}"
        return f"{e}"

