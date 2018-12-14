from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from members.models import User

class Storage(models.Model):
    STORAGE_STATE = (
    	('R', 'Requested'),
    	('AG','Auto granted (< month)'),
    	('OK','Approved'),
    	('1st','First extension'),
    	('NO','Denied'),
	('EX','Expired'),
    	('D', 'Remscinded'),
     )

    what = models.CharField(max_length=200)
    location = models.CharField(max_length=50, unique=True)
    extra_info = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    requested = models.DateField(auto_now_add=True)
    duration = models.IntegerField()
    state = models.CharField(max_length=1, choices=STORAGE_STATE)

    history = HistoricalRecords()

    def __str__(self):
        return what + " (" + owner.member.user.last_name + "@" + self.location + ")"

