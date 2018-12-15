from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Memberbox
from django.forms import ModelForm

class NewMemberboxForm(ModelForm):
    class Meta:
       model = Memberbox
       fields = [ 'location', 'extra_info', 'owner' ]

class MemberboxForm(ModelForm):
    class Meta:
       model = Memberbox
       fields = [ 'location', 'extra_info' ]
