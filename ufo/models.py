from django.conf import settings
# frmm django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.conf import settings

from django.db import models
from members.models import User

import datetime
import uuid
import os

import re

import logging
logger = logging.getLogger(__name__)

def ufo_generate_unique_name(instance,filename):
   return "ufo/"+str(uuid.uuid4())

def validate_unique_name(leaf_filename):
    regex = re.compile('^ufo/[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\.(png|jpg)$', re.I)
    match = regex.match(leaf_filename)
    return bool(match)

class Ufo(models.Model):
     UFO_STATE = (
           ('UNK', 'Unidentified'),
           ('OK', 'Claimed'),
           ('DEL', 'can be disposed'),
           ('DON', 'Donated to the space'),
     )
     image = models.ImageField(
#         upload_to=lambda instance, filename: "ufo/"+str(uuid.uuid4())
         upload_to=ufo_generate_unique_name
         )
     description = models.CharField(max_length=300, blank=True, null=True)

     state = models.CharField(max_length=4, choices=UFO_STATE, default='UNK', blank=True, null = True)

     deadline = models.DateField(blank=True, null = True)
     dispose_by_date = models.DateField(blank=True, null = True)

     lastChange =  models.DateField(blank=True, null = True)
     owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null = True)

     history = HistoricalRecords()

     def save(self, * args, ** kwargs):
         self.lastChange =  datetime.date.today()

         if not self.deadline:
                self.deadline =  datetime.date.today() + datetime.timedelta(settings.UFO_DEADLINE_DAYS)

         if not self.dispose_by_date:
                self.dispose_by_date = datetime.date.today() + datetime.timedelta(settings.UFO_DISPOSE_DAYS)

         if self.dispose_by_date < self.deadline:
               self.dispose_by_date = self.deadline + datetime.timedelta(1)

         return super(Ufo,self).save(*args, **kwargs)

     def delete(self, * args, ** kwargs):
         # Verify that we have what we thing we have - before we dare to 
         # use that value for an actual delete on this.
         #
         if not validate_unique_name(self.image.name):
             raise ValueError('The UFO filename does not match the required structure. Not deleting.')

         for p  in [ '', 'small_' ]:
            # We're using the relative path rather than the full
            # path so we can control the prefix.
            #
            f = settings.MEDIA_ROOT + '/' + p + self.image.name

            if not os.path.isfile(f):
                raise ValueError('The UFO image is not a file. Not deleting.')
                return None

            # Allow remove to raise its own exception.
            #
            os.remove(f)

         return super(Ufo,self).delete(*args, **kwargs)
