from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.conf import settings

from .models import PettycashTransaction, PettycashStation
import uuid

class UserChoiceField(forms.ModelChoiceField):
     def label_from_instance(self, obj):
         return "test {}".format(obj.name)

class PettycashPairForm(forms.Form):
    station = forms.ModelChoiceField(queryset=PettycashStation.objects.all())
    reason = forms.CharField(max_length=300, required=False,help_text='Reason for this change')

class PettycashTransactionForm(ModelForm):

    def __init__(self, *args, **kwargs):
       super(PettycashTransactionForm, self).__init__(*args, **kwargs)
       self.fields['src'].empty_label = settings.POT_LABEL
       self.fields['dst'].empty_label = settings.POT_LABEL

    class Meta:
       model = PettycashTransaction
       fields = [ 'src', 'dst', 'description', 'amount' ]

class PettycashDeleteForm(forms.Form):
    reason = forms.CharField(max_length=300, required=False,help_text='Reason for removing this transaction')
