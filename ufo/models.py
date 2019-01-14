from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.conf import settings

from django.db import models
from members.models import User

import datetime
import uuid
import os

class Ufo(models.Model):
     UFO_STATE = (
           ('UNK', 'Unidentified'),
           ('OK', 'Claimed'),
           ('DEL', 'can be disposed'),
           ('DON', 'Donated to the space'),
     )
     image = models.ImageField(
         upload_to=lambda instance, filename: "ufo/"+str(uuid.uuid4())
         )
     description = models.CharField(max_length=300, blank=True, null=True)

     state = models.CharField(max_length=4, choices=UFO_STATE, default='UNK', blank=True, null = True)
     lastChange =  models.DateField(blank=True, null = True)
     owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null = True)

     history = HistoricalRecords()

     def save(self, * args, ** kwargs):
         self.lastChange =  datetime.date.today()

         return super(Ufo,self).save(*args, **kwargs)

     # We let django cleanup do this. No need yet to do
     # modify - as we do not allow that yet.
     #
     # def delete(self, * args, ** kwargs):
     #    if os.path.isfile(self.image.path):
     #      os.remove(self.image.path)
     #    return super(Ufo,self).delte(*args, **kwargs)
