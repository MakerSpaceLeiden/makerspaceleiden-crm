from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Tag, clean_tag_string
from django.forms import ModelForm
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
