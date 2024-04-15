from datetime import timedelta

from django import forms
from django_flatpickr.schemas import FlatpickrOptions
from django_flatpickr.widgets import DatePickerInput, TimePickerInput

from .models import Motd


class MotdForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        _ = kwargs.pop("form_type", "create_message")
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
        self.fields["motd"].initial = ""
        self.fields["motd"].error_messages = {
            "required": "Required: Please enter the message text."
        }
        self.fields["motd_details"].error_messages = {
            "required": "Required: Please enter extra message info."
        }
        self.fields["motd_details"].initial = ""
        self.fields["motd_details"].required = False

    def clean(self):
        cleaned_data = super().clean()
        startdate = cleaned_data.get("startdate")
        enddate = cleaned_data.get("enddate")

        if startdate and enddate:
            difference = enddate - startdate

            # Check if the difference is greater than 2 weeks
            if difference > timedelta(weeks=2):
                raise forms.ValidationError(
                    "Maximum time limit: The start date and end date cannot be more then two weeks apart."
                )

    class Meta:
        model = Motd
        fields = [
            "startdate",
            "starttime",
            "enddate",
            "endtime",
            "motd",
            "motd_details",
        ]

        widgets = {
            "motd": forms.Textarea(attrs={"class": "form-control"}),
            "motd_details": forms.Textarea(attrs={"class": "form-control"}),
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
