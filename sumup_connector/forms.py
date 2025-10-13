from django import forms

from members.models import User


class DateInput(forms.DateInput):
    input_type = "date"


class CheckoutsForm(forms.Form):
    user = forms.ModelChoiceField(
        label="Limit search to user",
        queryset=User.objects.all(),
        required=False,
    )
    from_date = forms.DateField(
        widget=DateInput,
        help_text="Only show transactions on, and from this day onwards ",
        required=False,
    )
    until_date = forms.DateField(
        widget=DateInput,
        help_text="Only show transactions on , and before, this day",
        required=False,
    )

    OPTIONS = [
        ("0", "Completed transactions"),
        ("1", "Incomplete/canceled transactions"),
        ("2", "All"),
    ]

    state = forms.ChoiceField(
        choices=OPTIONS,
        initial="0",
        widget=forms.Select(),
        required=False,
        label="Transactions to show",
    )

    class Meta:
        fields = ["state", "from_date", "until_date", "user"]
