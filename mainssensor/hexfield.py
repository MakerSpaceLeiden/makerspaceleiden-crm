from django.db import models
from django import forms

import re

class HexFormField(forms.CharField):

    default_error_messages = {
        'invalid_hex': 'Enter a valid hex number: e.g. "DE12", the 0x prefix is optional; case is ignored.',
    }

    def clean(self, value):
        value = re.sub('.*x','',value,flags=re.IGNORECASE)
        # Humour BBC Micro's
        value = re.sub('^&','',value)

        if (not (value == '' and not self.required) and
                not re.match('^[A-Fa-f0-9]+$', value)):
            raise forms.ValidationError(self.error_messages['invalid_hex'])

        return value

class HexField(models.IntegerField):
    description = "Hexadecimal value"

    def get_prep_value(self, value):
        return int(value, 16)

    def to_python(self, value):
        if isinstance(value, str) or value is None:
            strout = value
        else:
            strout = hex(value)[2:]
            if (len(strout) < 4):
              strout = (4 - len(strout)) * '0' + strout 

        return strout

    def formfield(self, **kwargs):
        kwargs['widget'] = forms.TextInput
        return super().formfield(form_class = HexFormField, **kwargs)
        kwargs['form_class'] = HexFormField
        kwargs['max_length'] = 4
        return models.fields.Field.formfield(self, **kwargs)
