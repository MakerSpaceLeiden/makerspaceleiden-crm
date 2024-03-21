from django.conf import settings
import datetime

from django.db import models
from simple_history.models import HistoricalRecords

def get_deadline():
    return datetime.date.today() + datetime.timedelta(days=settings.MOTD_DEFAULT_SHOW_DAYS)

class Motd(models.Model):

    title = models.CharField(max_length=30)
    message = models.TextField(max_length=5000)

    date = models.DateField(default= datetime.date.today())
    show_until = models.DateField(default=get_deadline)

    history = HistoricalRecords()

    def __str__(self):
        return self.title
