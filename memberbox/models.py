from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from members.models import User

class Memberbox(models.Model):
    location = models.CharField(max_length=20, unique=True) # label = "Use left/right - shelf (top=1) - postion. E.g. R24 is the right set of shelves, second row from the top; 4th bin from the left.")
    extra_info = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    history = HistoricalRecords()

    def __str__(self):
        return "Box owned by " + owner.user.first_name + " " + owner.user.last_name + " at " + self.location

