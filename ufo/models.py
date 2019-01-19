from django.conf import settings
# frmm django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.conf import settings
from stdimage.models import StdImageField
from stdimage.validators import MinSizeValidator, MaxSizeValidator

from django.db.models.signals import pre_delete, pre_save
from stdimage.utils import pre_delete_delete_callback, pre_save_delete_callback

from django.db import models
from members.models import User
from makerspaceleiden.utils import upload_to_pattern
import datetime
import uuid
import os

import re

import logging
logger = logging.getLogger(__name__)

class Ufo(models.Model):
     UFO_STATE = (
           ('UNK', 'Unidentified'),
           ('OK', 'Claimed'),
           ('DEL', 'can be disposed'),
           ('DON', 'Donated to the space'),
     )
     image = StdImageField(upload_to=upload_to_pattern,
             variations=settings.IMG_VARIATIONS,validators=settings.IMG_VALIDATORS)
     description = models.CharField(max_length=300, blank=True, null=True)

     state = models.CharField(max_length=4, choices=UFO_STATE, default='UNK', blank=True, null = True)

     deadline = models.DateField(blank=True, null = True)
     dispose_by_date = models.DateField(blank=True, null = True)

     lastChange =  models.DateField(blank=True, null = True)
     owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null = True)

     history = HistoricalRecords()

     def url(self):
       return  settings.BASE + path()

     def path(self):
       return  settings.BASE + reverse('showufo', kwargs = { 'pk' :  self.id })

     def save(self, * args, ** kwargs):
         self.lastChange =  datetime.date.today()

         if not self.deadline:
                self.deadline =  datetime.date.today() + datetime.timedelta(settings.UFO_DEADLINE_DAYS)

         if not self.dispose_by_date:
                self.dispose_by_date = datetime.date.today() + datetime.timedelta(settings.UFO_DISPOSE_DAYS)

         if self.dispose_by_date < self.deadline:
               self.dispose_by_date = self.deadline + datetime.timedelta(1)

         return super(Ufo,self).save(*args, **kwargs)

# Handle image cleanup.
pre_delete.connect(pre_delete_delete_callback, sender=Ufo)
pre_save.connect(pre_save_delete_callback, sender=Ufo)
