from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.urls import reverse

from members.models import User

class PermitType(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description =  models.CharField(max_length=200)
    permit = models.ForeignKey(
	'self', 
	on_delete=models.CASCADE,
        blank=True, null=True,
	verbose_name='Permit reqiured',
        help_text='i.e. permit required by the issuer (default is none needed)"',
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description =  models.CharField(max_length=200,blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class NodeField(models.CharField):
    def get_prep_value(self, value):
        return str(value).lower()

class Machine(models.Model):
    name = models.CharField(max_length=40, unique=True)

    node_name  = NodeField(max_length=20,blank=True,help_text="Name of the controlling node")
    node_machine_name = NodeField(max_length=20, blank=True,help_text="Name of device or machine used by the node")

    description =  models.CharField(max_length=200,blank=True)
    location = models.ForeignKey(Location,related_name="is_located",on_delete=models.CASCADE, blank=True, null=True)
    requires_instruction = models.BooleanField(default=False)
    requires_form = models.BooleanField(default=False)
    requires_permit = models.ForeignKey(PermitType,related_name='has_permit',on_delete=models.CASCADE, blank=True, null=True)
    history = HistoricalRecords()

    def path(self):
       return  reverse('machine_overview', kwargs = { 'machine_id' :  self.id })

    def url(self):
       return  settings.BASE + url()

    def __str__(self):
        return self.name

class Entitlement(models.Model):
    active = models.BooleanField( default=False,)
    permit = models.ForeignKey(
	PermitType,
	on_delete=models.CASCADE,
        related_name='isRequiredToOperate',
    )
    holder = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='isGivenTo',
    )
    issuer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='isIssuedBy',
    )
    history = HistoricalRecords()

    def __str__(self):
        return str(self.holder) + '@' + self.permit.name +'(Active:'+str(self.active)+')'

    class EntitlementViolation(Exception):
        pass

    def save(self, *args, **kwargs):
        # rely on the contraints to bomb out if there is nothing in kwargs and self. and self.
        #
        if not self.issuer and request in kwargs:
                  self.issuer = kwargs['request'].user
              
        issuer_permit = PermitType.objects.get(pk = self.permit.pk)

        if 'request' in kwargs:
          if issuer_permit and not PermitType.objects.filter(permit=issuer_permit,holder=request.user):
             raise EntitlementViolation("issuer of this entitelment lacks the entitlement to issue it.")
       
        if self.active == None:
            # See if we can fetch an older approval for same that may already have
            # been activated. And grandfather it in.
            try:
               e = Entitlement.objects.get(permit = self.permit, holder = self.holder);
               self.active = e.active
            except EntitlementNotFound:
                pass

        # Notify the super users if this requires approval. Is this a good
        # place ? Or should bwe do this on a crontab ?
        #
        if not self.active and self.permit.permit:
            print("Should we send an email to notify Super users ?")

        return super(Entitlement, self).save(*args, **kwargs)

