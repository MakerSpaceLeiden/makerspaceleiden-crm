from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from .models import Ufo
import uuid

class NewUfoForm(ModelForm):
    class Meta:
       model = Ufo
       fields = [ 'image', 'description', ]

class UfoForm(ModelForm):
    class Meta:
       model = Ufo
       fields = [ 'description', 'owner', 'state' ]

class UfoZipUploadForm(forms.Form):
    zipfile = forms.FileField()
