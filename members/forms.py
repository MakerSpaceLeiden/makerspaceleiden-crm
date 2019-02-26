from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Tag, clean_tag_string, AuditRecord
from django.forms import ModelForm

from members.models import User
from unknowntags.models import Unknowntag

import re

class NewTagForm(ModelForm):
    class Meta:
       model = Tag
       fields = [ 'tag','owner','description' ]
       help_texts = {
          'description': 'Set by default to who/when it was added',
       }

class TagForm(ModelForm):
    class Meta:
       model = Tag
       fields = [ 'tag', 'description', 'last_used' ]
       help_texts = {
          'description': 'Optional - e.g. something like "my ov card", or "blue fob".',
       }

    def __init__(self, *args, **kwargs):
       self.canedittag = False
       self.isdelete = False

       if 'canedittag' in kwargs:
           self.canedittag = kwargs.pop('canedittag')

       if 'isdelete' in kwargs:
           self.isdelete = kwargs.pop('isdelete')
           self.canedittag = False

       super(TagForm, self).__init__(*args, **kwargs)

       self.fields['last_used'].widget.attrs['readonly'] = True
       self.fields['last_used'].help_text = '(not editable)'

       if not self.canedittag:
          self.fields['tag'].help_text = '(not editable)'
          self.fields['tag'].widget.attrs['readonly'] = True

       if self.isdelete:
          self.fields['description'].widget.attrs['readonly'] = True
          for k,f in self.fields.items():
                f.help_text = '(not editable during a delete)'

    def clean_tag(self):
        return clean_tag_string(self.cleaned_data['tag'])

class NewUserForm(forms.Form):
    first_name = forms.CharField(max_length=User._meta.get_field('first_name').max_length)
    last_name = forms.CharField(max_length=User._meta.get_field('last_name').max_length)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=User._meta.get_field('phone_number').max_length, 
	required=False, help_text="Optional; only visible to the trustees and board delegated administrators")
    tag = forms.ModelChoiceField(queryset=Unknowntag.objects.all(), required = False, help_text="Optional. Leave blank to add later.")
    activate_doors = forms.BooleanField(initial = True, help_text='Also give this user door permits if they did not have it yet. Only applicable if above tag is specified.') 

class NewAuditRecordForm(ModelForm):
   return_to = forms.CharField(widget = forms.HiddenInput())

   class Meta:
      model = AuditRecord
      fields = [ 'action', ]
      help_texts = {
          'action': 'Reason why you need to become admin; e.g. "debug an issue", "fix user record", "add a mailinglist", "adjust a tag", etc.',
      }
