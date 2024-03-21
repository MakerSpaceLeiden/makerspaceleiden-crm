from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

import models

class MotDForm(ModelForm):
    class Meta:
        model = MotD
