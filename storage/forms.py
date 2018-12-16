from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Storage
from django.forms import ModelForm

class StorageForm(ModelForm):
    class Meta:
       model = Storage
       fields = [ 'owner', 'what', 'location', 'extra_info', 'duration' ]
       labels = { 
          'extra_info': 'Justification or explanation',
       }
       help_text = {
          'duration': 'days; short storage request (under 30 days) get automatic approval.',
       }
    def __init__(self, storageOrFormOrNone, *args, **kwargs):
       super(ModelForm, self).__init__(storageOrFormOrNone, *args, **kwargs)

       storage = None
       if storageOrFormOrNone and isinstance(storageOrFormOrNone,Storage):
          storage = storageOrFormOrNone

       if not storage:
          return

       if storage:
          del self.fields['owner']

       if not storage.location_updatable():
          del self.fields['location'] 

       if not storage.justification_updatable():
          del self.fields['extra_info'] 

       if not storage.editable():
          self.fields = []

