from django import forms
from django.forms import ModelForm
from django.conf import settings

from members.models import User
from .models import Unknowntag


class SelectUserForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    activate_doors = forms.BooleanField(
        initial=True,
        help_text="Also give this user door permits if they did not have it yet.",
    )


class SelectTagForm(forms.Form):
    tag = forms.ModelChoiceField(queryset=Unknowntag.objects.all())
    activate_doors = forms.BooleanField(
        initial=True,
        help_text="Also give this user door permits if they did not have it yet.",
    )
