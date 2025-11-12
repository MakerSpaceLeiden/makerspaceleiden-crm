from datetime import datetime

from dateutil import rrule
from django import forms
from django.core.exceptions import ValidationError
from django_flatpickr.widgets import DateTimePickerInput

from .models import Agenda


class AgendaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        _ = kwargs.pop("form_type", "create_agenda_item")
        super().__init__(*args, **kwargs)
        self.fields["startdatetime"].error_messages = {
            "required": "Required: Please enter the start date and time."
        }
        self.fields["enddatetime"].error_messages = {
            "required": "Required: Please enter the end date and time."
        }
        self.fields["item_title"].initial = ""
        self.fields["item_title"].error_messages = {
            "required": "Required: Please enter the agenda item title."
        }

    def clean(self):
        cleaned_data = super().clean()
        startdate = cleaned_data.get("startdate")
        starttime = cleaned_data.get("starttime")
        enddate = cleaned_data.get("enddate")
        endtime = cleaned_data.get("endtime")

        # Validate the recurrence rule
        recurrences = cleaned_data.get("recurrences")
        if recurrences != "":
            try:
                _ = rrule.rrulestr(recurrences)
            except ValueError:
                raise ValidationError("Invalid recurrence rule")

        # Check if both start date/time and end date/time are provided
        if startdate and starttime and enddate and endtime:
            start_datetime = datetime.combine(startdate, starttime)
            end_datetime = datetime.combine(enddate, endtime)

            # Check if start datetime is after end datetime
            if start_datetime > end_datetime:
                raise ValidationError("The start time should be before the end time.")

    class Meta:
        model = Agenda
        fields = [
            "startdatetime",
            "enddatetime",
            "item_title",
            "item_details",
            "recurrences",
            "location",
        ]

        widgets = {
            "item_title": forms.Textarea(attrs={"class": "form-control"}),
            "item_details": forms.Textarea(attrs={"class": "form-control"}),
            "startdatetime": DateTimePickerInput(attrs={"class": "datetime-input"}),
            "enddatetime": DateTimePickerInput(attrs={"class": "datetime-input"}),
            "recurrences": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.Select(attrs={"class": "form-control"}),
        }


class AgendaStatusForm(forms.ModelForm):
    class Meta:
        model = Agenda
        fields = ["status"]

    def save(self, user):
        self.instance.set_status(self.cleaned_data["status"], user)

        return super().save(commit=True)
