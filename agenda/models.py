from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from members.models import User

CEST = ZoneInfo("Europe/Amsterdam")  # Handles both CET and CEST


class Agenda(models.Model):
    _startdatetime = models.DateTimeField(null=True)
    startdate = models.DateField(null=True)
    starttime = models.TimeField(null=True)
    _enddatetime = models.DateTimeField(null=True)
    enddate = models.DateField(null=True)
    endtime = models.TimeField(null=True)
    item_title = models.TextField(max_length=600, default="")
    item_details = models.TextField(max_length=5000, blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    history = HistoricalRecords()

    @property
    def start_datetime(self):
        if self._startdatetime:
            return self._startdatetime
        if self.startdate and self.starttime:
            dt = datetime.combine(self.startdate, self.starttime)
            if timezone.is_naive(dt):
                dt = dt.replace(tzinfo=CEST)
            return dt.astimezone(timezone.utc)
        return None

    @property
    def end_datetime(self):
        if self.enddate and self.endtime:
            dt = datetime.combine(self.enddate, self.endtime)
            if timezone.is_naive(dt):
                dt = dt.replace(tzinfo=CEST)
            return dt.astimezone(timezone.utc)
        return None

    def _get_utc_from_cest_date_and_time(self, date, time):
        if date and time:
            dt = datetime.combine(date, time)
            if timezone.is_naive(dt):
                dt = dt.replace(tzinfo=CEST)
            return dt.astimezone(timezone.utc)

        return None

    def save(self, *args, **kwargs):
        # Compute _startdatetime from startdate and starttime (assumed CE(S)T)
        self._startdatetime = self._get_utc_from_cest_date_and_time(
            self.startdate, self.starttime
        )
        self._enddatetime = self._get_utc_from_cest_date_and_time(
            self.enddate, self.endtime
        )

        super().save(*args, **kwargs)
