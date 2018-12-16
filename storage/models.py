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
    location = models.CharField(max_length=50)

    extra_info = models.TextField(max_length=1000)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    requested = models.DateField(auto_now_add=True)
    duration = models.IntegerField(default=30, help_text = 'days')

    state = models.CharField(max_length=4, choices=STORAGE_STATE)

    extends = models.OneToOneField('self', on_delete=models.CASCADE,blank=True, null=True)

    # Auto calculated
    lastdate = models.DateField(blank=True, null=True)
    history = HistoricalRecords()

    def enddate(self):
        return self.requested + datetime.timedelta( days = self.duration)

    def expired(self):
        return self.enddate() < datetime.date.today()

    def location_updatable(self): # we can update the location 
        return self.state in ('OK', 'R', '1st', 'AG' )

    def justification_updatable(self): # we can update the location 
        return self.state in ('R', '1st')

    def extendable(self): # we can ask for an extention (anew)
        return self.state in ('OK', 'AG' )

    def editable(self): # we can still change anything
        return self.state in ('R') 

    def deletable(self):
        return self.state in ('R','OK','1st','AG')

    def __str__(self):
        return self.what + "@" + self.location

    class AgainstTheRules(Exception):
        pass

    def file_for_extension(self):
        if not self.extendable:
            raise AgainstTheRules('Cannot file an extension on '+self.state+', needs to be OK/AG')

        n = Storage(self)
        n.state = '1st'
        n.extends = self
        n.save()

    def apply_rules(self):
        s = self.state

        if self.state == '':
             self.changeReason = '[rule] State set to R'
             self.state = 'R'

        if self.state == 'R' and self.duration <= 31:
             self.changeReason = '[rule] Auto approved (month or less)'
             self.state = 'AG'

        if self.expired():
             self.changeReason = '[rule] Expired -- been there too long'
             self.state = 'EX'

        if s != self.state:
           self.save()

        return
