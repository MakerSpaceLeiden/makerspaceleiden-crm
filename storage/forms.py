from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Storage
from django.forms import ModelForm

class StorageForm(ModelForm):
    extension_rq = forms.BooleanField(
      label="Request an extra month:", 
      required=False,
    )
    class Meta:
       model = Storage
       fields = [ 'what', 'location', 'extra_info', 'extension_rq' ]
       labels = { 'extra_info': 'Justification or explanation' }
 
class NewStorageForm(ModelForm):
    class Meta:
       model = Storage
       fields = [ 'owner', 'what', 'location', 'extra_info', 'duration' ]
