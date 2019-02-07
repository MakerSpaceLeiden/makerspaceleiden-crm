from django.conf import settings
from django.db import models
import datetime

class Unknowntag(models.Model):
   tag = models.CharField(max_length=30) 
   last_used = models.DateTimeField(auto_now=True)

   def save(self, * args, ** kwargs):
      r = super(Unknowntag,self).save(*args, **kwargs)

      stale_tags = Unknowntag.objects.all().order_by('-last_used')[settings.UT_COUNT_CUTOFF:]

      for stale_tag in stale_tags:
          stale_tag.delete()

      return r

   def __str__(self):
         return "{} swiped on {}".format(self.tag, self.last_used.strftime("%Y-%m-%d %H:%M:%S"))
