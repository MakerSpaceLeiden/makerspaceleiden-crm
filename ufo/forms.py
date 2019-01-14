from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm
from django.conf import settings


from .models import Ufo
import uuid

class NewUfoForm(ModelForm):
    class Meta:
       model = Ufo
       fields = [ 'image', 'description', 'deadline', 'dispose_by_date' ]

class UfoForm(ModelForm):
    class Meta:
       model = Ufo
       fields = [ 'description', 'owner', 'deadline', 'dispose_by_date', 'state' ]

class UfoZipUploadForm(forms.Form):
    zipfile = forms.FileField(required=False)
    description = forms.CharField(max_length=300, required=False,help_text='Will be auto filled if left empty')
    deadline = forms.DateField(required=False,help_text='Will be auto calcuated if left empty (%d days from now)' % settings.UFO_DEADLINE_DAYS)
    dispose_by_date = forms.DateField(required=False,help_text='Will be auto calcuated if left empty (%d after the above deadline)' % settings.UFO_DISPOSE_DAYS)
