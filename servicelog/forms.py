from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from servicelog.models import Servicelog


class ServicelogForm(forms.ModelForm):
    # Keep separate / not part of th emodel so we can log this in the machine ?
    out_of_order = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Is the machine broken; and should not not be used until fixed ? <p>For example set this if it is dangerous to use (like when a safety feature is broken, something can come loose, can cut someone, etc). Or if it is highly likely to damange the next persons work (like when there is a knick in one of the blades that will ruin the work?)",
    )

    def __init__(self, *args, **kwargs):
        self.canreturntoservice = False
        if "canreturntoservice" in kwargs:
            self.canreturntoservice = kwargs.pop("canreturntoservice")

        super(ServicelogForm, self).__init__(*args, **kwargs)

        if not self.canreturntoservice:
            self.fields["situation"].choices = [
                e for e in self.fields["situation"].choices if e[0] != Servicelog.FIXED
            ]
            self.fields[
                "situation"
            ].help_text = "You cannot mark this machine as `fixed' unless you are able to give instruction on it."

    class Meta:
        model = Servicelog
        # We fill out machine, report, etc away from the form.
        fields = ["description", "image", "situation", "out_of_order"]
