from django.db import models
from simple_history.models import HistoricalRecords

from members.models import User


class Agenda(models.Model):
    startdate = models.DateField(null=True)
    starttime = models.TimeField(null=True)
    enddate = models.DateField(null=True)
    endtime = models.TimeField(null=True)
    item_title = models.TextField(max_length=600, default="")
    item_details = models.TextField(max_length=5000, blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    history = HistoricalRecords()

    @property
    def start_datetime(self):
        if self.startdate and self.starttime:
            from datetime import datetime

            return datetime.combine(self.startdate, self.starttime)
        return None

    @property
    def end_datetime(self):
        if self.enddate and self.endtime:
            from datetime import datetime

            return datetime.combine(self.enddate, self.endtime)
        return None
