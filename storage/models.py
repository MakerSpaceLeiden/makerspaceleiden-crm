from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from members.models import User
import datetime

class Storage(models.Model):
    STORAGE_STATE = (
    	('R', 'Requested'),
    	('AG','Auto granted (<= month)'),
    	('1st','First extension'),
    	('OK','Approved'),
    	('NO','Denied'),
	('EX','Expired'),
    	('D', 'Rescinded'),
     )

    what = models.CharField(max_length=200)
    location = models.CharField(max_length=50, unique=True)
    extra_info = models.TextField(max_length=1000)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    requested = models.DateField(auto_now_add=True)
    duration = models.IntegerField(default=30, help_text = 'days')
    state = models.CharField(max_length=4, choices=STORAGE_STATE)

    history = HistoricalRecords()

    def enddate(self):
        return self.requested + datetime.timedelta( days = self.duration)

    def expired(self):
        return self.enddate() < datetime.date.today()

    def editable(self):
        return self.state in ('OK', 'R', '1st', 'AG' )

    def __str__(self):
        return self.what + "@" + self.location

