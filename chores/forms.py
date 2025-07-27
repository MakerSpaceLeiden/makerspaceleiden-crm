from datetime import datetime

from django import forms

from .models import Chore


class ChoreForm(forms.ModelForm):
    frequency = forms.IntegerField(
        required=True,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    starting_from = forms.DateTimeField(
        required=False,
        input_formats=["%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"class": "form-control", "placeholder": "YYYY/MM/DD HH:MM"},
            format="%Y/%m/%d %H:%M",
        ),
    )

    cron = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "0 22 * * sun"}
        ),
    )

    duration_value = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    duration_unit = forms.CharField(
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select h-100 ms-2"},
            choices=[
                ("h", "hours"),
                ("d", "days"),
                ("w", "weeks"),
            ],
        ),
    )

    def __init__(self, *args, **kwargs):
        _ = kwargs.pop("form_type", "create_chore")
        super().__init__(*args, **kwargs)
        self.fields["name"].initial = ""
        self.fields["name"].error_messages = {
            "required": "Required: Please enter the chore name."
        }
        self.fields["description"].initial = ""
        self.fields["description"].error_messages = {
            "required": "Required: Please enter the chore description."
        }
        self.fields["wiki_url"].initial = ""
        self.fields["wiki_url"].error_messages = {
            "required": "Required: Please enter the wiki URL."
        }

        configuration = self.instance.configuration
        if isinstance(configuration, str):
            configuration = {}

        self.fields["starting_from"].initial = configuration.get(
            "events_generation", {}
        ).get("starting_time", datetime.now())
        self.fields["starting_from"].error_messages = {
            "required": "Required: Please enter the starting time.",
            "invalid": "Required: Please enter a valid starting time.",
        }
        self.fields["cron"].initial = configuration.get("events_generation", {}).get(
            "crontab", ""
        )
        self.fields["frequency"].initial = configuration.get(
            "events_generation", {}
        ).get("take_one_every", 1)

    class Meta:
        model = Chore
        fields = [
            "name",
            "description",
            "wiki_url",
            # "frequency",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "wiki_url": forms.URLInput(attrs={"class": "form-control"}),
            # "frequency": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        frequency = self.cleaned_data.get("frequency")
        # Process or use frequency as needed before saving the instance
        # For example, set some attribute on the instance or trigger other logic:
        instance.configuration = {
            "events_generation": {
                "take_one_every": frequency,
                "event_type": "recurrent",
                "starting_time": self.cleaned_data.get("starting_from").strftime(
                    "%Y/%m/%d %H:%M"
                ),
                "crontab": self.cleaned_data.get("cron"),
                "duration": f"P{self.cleaned_data.get('duration_value')}{self.cleaned_data.get('duration_unit').upper()}",
            }
        }
        if commit:
            instance.save()
        return instance

    def get_success_url(self):
        return self.instance.get_absolute_url()
