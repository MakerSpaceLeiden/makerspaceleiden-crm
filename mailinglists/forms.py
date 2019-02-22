from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.conf import settings

from .models import Subscription

class SubscriptionForm(ModelForm):
    class Meta:
       model = Subscription
       labels = { 'active': 'Currenty Subcribed',
                  'digest': 'Receive in digest form' 
       }
       fields = [ 'active', 'digest', ]

