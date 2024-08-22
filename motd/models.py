from django.db import models
from simple_history.models import HistoricalRecords

from members.models import User


class Motd(models.Model):
    startdate = models.DateField(null=True)
    starttime = models.TimeField(null=True)
    enddate = models.DateField(null=True)
    endtime = models.TimeField(null=True)
    motd = models.TextField(max_length=600, default="")
    motd_details = models.TextField(max_length=5000, blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    history = HistoricalRecords()
