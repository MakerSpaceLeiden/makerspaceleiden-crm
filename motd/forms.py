from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

import models

class MotdForm(ModelForm):
    class Meta:
        model = Motd
