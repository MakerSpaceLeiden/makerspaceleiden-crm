from django.db import models

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

class Mainssensor(models.Model):
   tag = models.IntegerField(unique=True,help_text="Unique tag id (decimal)")
   name = models.CharField(max_length=30) 
   description  = models.CharField(max_length=200) 

   def __str__(self):
         return "{}({})".format(self.name, self.tag);
