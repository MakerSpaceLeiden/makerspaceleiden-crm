from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.conf import settings

from .models import PettycashTransaction
import uuid

class PettycashTransactionForm(ModelForm):
    class Meta:
       model = PettycashTransaction
       fields = [ 'src', 'dst', 'description', 'amount' ]
