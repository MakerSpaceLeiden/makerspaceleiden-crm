from django.db import models

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .hexfield import HexField

class Mainssensor(models.Model):
   tag = HexField(unique=True,help_text="Unique tag id (4 digit hex)")
   name = models.CharField(max_length=30) 
   description  = models.CharField(max_length=200) 

   def __str__(self):
        v  = self.tag
        if isinstance(v, str):
          v = int(self.tag, 16)
        return "0x{:04X}: {}".format(v, self.name)
