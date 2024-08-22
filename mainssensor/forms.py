from django.forms import ModelForm

from .models import Mainssensor


class NewMainssensorForm(ModelForm):
    class Meta:
        model = Mainssensor
        fields = ["name", "tag", "description"]
        help_texts = {"tag": "Tag value needs to be hexadecimal; eg. 0x8001 or 8001"}


class MainssensorForm(ModelForm):
    class Meta:
        model = Mainssensor
        fields = ["name", "tag", "description"]
