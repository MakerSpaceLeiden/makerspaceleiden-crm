from django import forms
from django.contrib.auth.forms import UserCreationForm
from members.models import User
from django.forms import ModelForm


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "image"]
        help_texts = {
            "email": "When you change this field; you will get a verification email to your new address. And your old address and the trustee's are sent a notice of this change."
        }


class SignalNotificationSettingsForm(ModelForm):
    class Meta:
        model = User
        fields = ["phone_number", "uses_signal"]
        help_texts = {
            "phone_number": "In order to use Signal, you need to enter your phone number including the country code.",
            "uses_signal": "Check this box if you want to use Signal.",
        }


class EmailNotificationSettingsForm(ModelForm):
    class Meta:
        model = User
        fields = ["always_uses_email"]


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    last_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    email = forms.EmailField(
        max_length=254, help_text="Required. Inform a valid email address."
    )
    phone_number = forms.CharField(
        max_length=40,
        required=False,
        help_text="Optional; only visible to the trustees and board delegated administrators",
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class TabledCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = "multiple_inputs_tabled.html"
