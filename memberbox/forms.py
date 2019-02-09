from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Memberbox
from django.forms import ModelForm
import re

class NewMemberboxForm(ModelForm):
    class Meta:
       model = Memberbox
       fields = [ 'image', 'location', 'extra_info', 'owner' ]
       help_texts = {
          'image': 'Optional - and you can always add it later (recommended though)',
       }

class MemberboxForm(ModelForm):
    class Meta:
       model = Memberbox
       fields = [ 'image', 'location', 'extra_info', 'owner' ]

    # Try to keep the boxes in the cupboard all in uppercase
    # and let other things be whatever they got entered as.
    #
    def clean_location(self):
        loc = self.cleaned_data['location'].upper()
        if re.search(r'^([LR]{1})(\d{1})(\d{1})$', loc):
           return loc
        return self.cleaned_data['location']
