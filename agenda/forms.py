from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django_flatpickr.schemas import FlatpickrOptions
from django_flatpickr.widgets import DatePickerInput, TimePickerInput

from .models import Agenda


class AgendaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        _ = kwargs.pop("form_type", "create_agenda_item")
        super().__init__(*args, **kwargs)
        self.fields["startdate"].error_messages = {
            "required": "Required: Please enter the start date."
        }
        self.fields["starttime"].error_messages = {
            "required": "Required: Please enter the start time."
        }
        self.fields["enddate"].error_messages = {
            "required": "Required: Please enter the end date."
        }
        self.fields["endtime"].error_messages = {
            "required": "Required: Please enter the end time."
        }
        self.fields["item_title"].initial = ""
        self.fields["item_title"].error_messages = {
            "required": "Required: Please enter the agenda item title."
        }

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data = super().clean()
        startdate = cleaned_data.get("startdate")
        starttime = cleaned_data.get("starttime")
        enddate = cleaned_data.get("enddate")
        endtime = cleaned_data.get("endtime")

        # Check if both start date/time and end date/time are provided
        if startdate and starttime and enddate and endtime:
            start_datetime = datetime.combine(startdate, starttime)
            end_datetime = datetime.combine(enddate, endtime)

            # Check if start datetime is after end datetime
            if start_datetime >= end_datetime:
                raise ValidationError("The start time should be before the end time.")

    class Meta:
        model = Agenda
        fields = [
            "startdate",
            "starttime",
            "enddate",
            "endtime",
            "item_title",
            "item_details",
        ]

        widgets = {
            "item_title": forms.Textarea(attrs={"class": "form-control"}),
            "item_details": forms.Textarea(attrs={"class": "form-control"}),
            "startdate": DatePickerInput(
                options=FlatpickrOptions(
                    altFormat="d-m-Y",
                ),
                attrs={"class": "date-input"},
            ),
            "starttime": TimePickerInput(
                options=FlatpickrOptions(
                    time_24hr=True,
                    altFormat="H:i",
                    minuteIncrement=1,
                ),
                attrs={"class": "date-input"},
            ),
            "enddate": DatePickerInput(
                options=FlatpickrOptions(
                    altFormat="d-m-Y",
                ),
                attrs={"class": "date-input"},
            ),
            "endtime": TimePickerInput(
                options=FlatpickrOptions(
                    time_24hr=True,
                    altFormat="H:i",
                    minuteIncrement=1,
                ),
                attrs={"class": "date-input"},
            ),
        }
