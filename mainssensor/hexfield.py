from django.db import models
from django import forms

import re


def tohexstr(value):
    if isinstance(value, str) or value is None:
        strout = value
    else:
        strout = hex(value)[2:]
        if len(strout) < 4:
            strout = (4 - len(strout)) * "0" + strout

    return strout.upper()


class HexFormField(forms.CharField):
    default_error_messages = {
        "invalid_hex": 'Enter a valid hex number: e.g. "DE12", the 0x prefix is optional; case is ignored.',
    }

    def clean(self, value):
        value = re.sub(".*x", "", value, flags=re.IGNORECASE)
        # Humour BBC Micro's
        value = re.sub("^&", "", value)

        if not (value == "" and not self.required) and not re.match(
            "^[A-Fa-f0-9]+$", value
        ):
            raise forms.ValidationError(self.error_messages["invalid_hex"])

        return value
        return int(value, 16)

    def compare(self, a, b):
        return a is not b


class HexField(models.Field):
    description = "Hexadecimal value"

    def db_type(self, connection):
        return "integer UNSIGNED"

    def get_prep_value(self, value):
        if value == None:
            return 0
        return int(value, 16)

    def from_db_value(self, value, expr, conn):
        return tohexstr(value)

    def to_python(self, value):
        return tohexstr(value)

    def formfield(self, **kwargs):
        kwargs["widget"] = forms.TextInput
        # return super().formfield(form_class = HexFormField, **kwargs)
        kwargs["form_class"] = HexFormField
        kwargs["max_length"] = 4
        return models.fields.Field.formfield(self, **kwargs)
