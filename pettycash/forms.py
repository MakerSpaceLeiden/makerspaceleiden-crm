from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.conf import settings

from .models import PettycashTransaction
import uuid

class UserChoiceField(forms.ModelChoiceField):
     def label_from_instance(self, obj):
         return "test {}".format(obj.name)

class PettycashTransactionForm(ModelForm):

    def __init__(self, *args, **kwargs):
       super(PettycashTransactionForm, self).__init__(*args, **kwargs)
       self.fields['src'].empty_label = settings.POT_LABEL
       self.fields['dst'].empty_label = settings.POT_LABEL

    class Meta:
       model = PettycashTransaction
       fields = [ 'src', 'dst', 'description', 'amount' ]


