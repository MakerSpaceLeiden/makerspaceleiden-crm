from django import forms
from django.conf import settings
from django.forms import ModelForm
from djmoney.models.validators import MaxMoneyValidator, MinMoneyValidator

from .models import (
    PettycashReimbursementRequest,
    PettycashSku,
    PettycashStation,
    PettycashTransaction,
)


# As payments on the terminals are always done via the API, limit
# the amounts on creation to the current max. This is not really
# compliance reasons (that is done in the save/transaction) - but
# just to prevent someone from creating something that is too
# expensive to buy (without editing the settings).
#
class PettycashSkuForm(forms.ModelForm):
    class Meta:
        model = PettycashSku
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We do this here; rather than in models; so we can pick up the actual value.
        self.fields["amount"].help_text = (
            f"Max is set to {settings.MAX_PAY_API}, change this in settings.py. This is the maximum payment that the payment terminals will be able to accept. If you enter a higher value - it will be capped to this value.",
        )

    #       # for some reason - below does not work. Not does doing this in Model.
    #       self.fields["amount"].fields[0].max_value = settings.MAX_PAY_API

    # Can only give a error by raising an exception; so cap the
    # value for now.
    def clean_amount(self):
        amt = self.cleaned_data.get("amount")
        if amt > settings.MAX_PAY_API:
            return settings.MAX_PAY_API
        return amt


class UserChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "test {}".format(obj.name)


class PettycashPairForm(forms.Form):
    station = forms.ModelChoiceField(queryset=PettycashStation.objects.all())
    reason = forms.CharField(
        max_length=300, required=False, help_text="Reason for this change"
    )


# In some cases - we allow the trustees a higher limit. This is visible in both the form
# and policed in the backend. Below base class shows this in the user interface.
#
class PettycashRequestFormBase(ModelForm):
    def __init__(self, *args, **kwargs):
        self.max_val = settings.MAX_PAY_CRM.amount
        alternative_text = "Above that; contact the trustees directly (%s)" % (
            settings.TRUSTEES
        )
        if "is_privileged" in kwargs:
            if kwargs["is_privileged"]:
                self.max_val = settings.MAX_PAY_TRUSTEE.amount
                alternative_text = "Above that - split the transaction."
            kwargs.pop("is_privileged")

        super(PettycashRequestFormBase, self).__init__(*args, **kwargs)

        self.fields["amount"].help_text = (
            "This system will only accept amounts up to %s. %s"
            % (
                self.max_val,
                alternative_text,
            )
        )
        self.fields["amount"].validators = [
            MinMoneyValidator(0),
            MaxMoneyValidator(self.max_val),
        ]


class PettycashTransactionForm(PettycashRequestFormBase):
    def __init__(self, *args, **kwargs):
        super(PettycashTransactionForm, self).__init__(*args, **kwargs)
        self.fields["src"].empty_label = settings.POT_LABEL
        self.fields["dst"].empty_label = settings.POT_LABEL

    class Meta:
        model = PettycashTransaction
        fields = ["src", "dst", "description", "amount"]


class PettycashDeleteForm(forms.Form):
    reason = forms.CharField(
        max_length=300, required=False, help_text="Reason for removing this transaction"
    )


class PettycashPayoutRequestForm(PettycashRequestFormBase):
    def __init__(self, *args, **kwargs):
        super(PettycashPayoutRequestForm, self).__init__(*args, **kwargs)
        self.fields["description"].initial = "Afromen / Surplus"

    class Meta:
        model = PettycashReimbursementRequest
        fields = ["src", "description", "amount", "date"]
        labels = {"src": "Account"}
        help_texts = {
            "src": "From whose account (i.e. yousually your own) the money should be taken that is wired to you."
        }


class PettycashReimbursementRequestForm(PettycashRequestFormBase):
    def __init__(self, *args, **kwargs):
        super(PettycashReimbursementRequestForm, self).__init__(*args, **kwargs)

    class Meta:
        model = PettycashReimbursementRequest
        fields = ["dst", "description", "amount", "date", "viaTheBank", "scan"]


class PettycashReimburseHandleForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())
    reason = forms.CharField(
        max_length=300,
        required=False,
        help_text="Reason for rejecting this reimbursement request",
    )


class CamtUploadForm(forms.Form):
    cam53file = forms.FileField(
        label="Select a file", help_text="CAM52 (xml) export of transactions"
    )


class ImportProcessForm(forms.Form):
    def __init__(self, valids, *args, **kwargs):
        super(ImportProcessForm, self).__init__(*args, **kwargs)
        i = 0
        for tx in valids:
            self.fields["ok_%d" % i] = forms.BooleanField(
                initial=True, required=False, label=""
            )
            self.fields["d_amount_%d" % i] = forms.CharField(
                initial=tx["amount"],
                required=True,
                label="",
                disabled=True,
                widget=forms.TextInput(attrs={"size": 6}),
            )
            self.fields["d_user_%d" % i] = forms.CharField(
                initial=tx["user"],
                required=True,
                label="",
                disabled=True,
                widget=forms.TextInput(attrs={"size": 20}),
            )
            self.fields["d_description_%d" % i] = forms.CharField(
                initial=tx["description"],
                required=True,
                label="",
                disabled=True,
                widget=forms.TextInput(attrs={"size": 30}),
            )
            self.fields["d_description_%d" % i] = forms.CharField(
                initial=tx["description"], required=True, label="", disabled=True
            )
            self.fields["d_change_reason_%d" % i] = forms.CharField(
                initial=tx["change_reason"],
                required=True,
                label="",
                disabled=True,
                help_text="<p>",
                widget=forms.TextInput(attrs={"size": 120}),
            )

            self.fields["amount_%d" % i] = forms.CharField(
                initial=tx["amount"].amount, widget=forms.HiddenInput()
            )
            self.fields["user_%d" % i] = forms.CharField(
                initial=tx["user"].id, widget=forms.HiddenInput()
            )
            self.fields["description_%d" % i] = forms.CharField(
                initial=tx["description"], widget=forms.HiddenInput()
            )
            self.fields["description_%d" % i] = forms.CharField(
                initial=tx["description"], widget=forms.HiddenInput()
            )
            self.fields["change_reason_%d" % i] = forms.CharField(
                initial=tx["change_reason"], widget=forms.HiddenInput()
            )
            i = i + 1
        self.fields["vals"] = forms.CharField(initial=i, widget=forms.HiddenInput())
