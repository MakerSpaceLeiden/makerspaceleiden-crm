from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Mainssensor
from django.forms import ModelForm
import re


class NewMainssensorForm(ModelForm):
    class Meta:
        model = Mainssensor
        fields = ["name", "tag", "description"]
        help_texts = {"tag": "Tag value needs to be hexadecimal; eg. 0x8001 or 8001"}


class MainssensorForm(ModelForm):
    class Meta:
        model = Mainssensor
        fields = ["name", "tag", "description"]
