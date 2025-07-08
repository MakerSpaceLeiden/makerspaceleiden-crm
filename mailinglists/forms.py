from django.forms import ModelForm

from .models import Subscription


class SubscriptionForm(ModelForm):
    class Meta:
        model = Subscription
        labels = {"active": "Subcribed"}
        fields = [
            "active",
            "digest",
        ]

    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)

        if kwargs is not None and "instance" in kwargs:
            sub = kwargs["instance"]
            if sub and sub.mailinglist.mandatory:
                self.fields["active"].value = True
                self.fields["active"].disabled = True
                self.fields[
                    "active"
                ].help_text = "This list is mandatory for all members. It cannot be disabled. Contact the trustees for exceptions."
