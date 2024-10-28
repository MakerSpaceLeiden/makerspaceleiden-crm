from django import forms

from servicelog.models import Servicelog


class ServicelogForm(forms.ModelForm):
    # Keep separate / not part of th emodel so we can log this in the machine ?
    out_of_order = forms.BooleanField(
        required=False,
        initial=True,
        help_text="<p>Is the machine currently broken and should not be used until it is fixed?</p> <p><strong>Check this box if:</strong></p> <ul> <li><small>The machine is dangerous to use (e.g., a broken safety feature, risk of injury, or potential damage to work) or,</small></li> <li><small>it is likely to damage the next person’s work (e.g., a knick in a blade).</small></li> </ul><p><strong>Uncheck this box if: </strong></p> <ul> <li><small>The machine is no longer out of order and is safe to use.</small></li></ul>",
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
