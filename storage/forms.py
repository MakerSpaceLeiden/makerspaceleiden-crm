import logging

from django import forms
from django.forms import ModelForm

from .models import Storage

logger = logging.getLogger(__name__)


class ConfirmForm(forms.Form):
    pk = forms.IntegerField(disabled=True, widget=forms.HiddenInput())


class StorageForm(ModelForm):
    class Meta:
        model = Storage
        fields = ["owner", "what", "image", "location", "extra_info", "duration"]
        labels = {
            "extra_info": "Justification or explanation",
        }
        help_texts = {
            "image": "Optional - but highly recommended!",
            "location": "E.g. 'on the project table', 'on top of the CV cabinet', etc",
            "duration": "In days; short storage request (under 30 days) get automatic approval.",
        }

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        storage = None

        if kwargs is not None and "instance" in kwargs:
            storage = kwargs["instance"]

        if not storage:
            return

        if storage:
            del self.fields["owner"]

        if not storage.location_updatable():
            del self.fields["location"]

        if not storage.justification_updatable():
            del self.fields["extra_info"]

        if not storage.editable():
            del self.fields["what"]
            del self.fields["duration"]
