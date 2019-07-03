from django.db import models

from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from django.urls import reverse
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string, get_template
from django.contrib.sites.shortcuts import get_current_site

from members.models import User
from django.contrib.sites.models import Site

import logging
logger = logging.getLogger(__name__)

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

    def hasThisPermit(self, user):
        e = Entitlement.objects.all().filter(holder=user,permit=self).first
        if e and e.active == True:
            return True
        return False
           
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

    out_of_order = models.BooleanField(default=False)

    history = HistoricalRecords()

    def path(self):
       return  reverse('machine_overview', kwargs = { 'machine_id' :  self.id })

    def url(self):
       return  settings.BASE + url()

    def __str__(self):
        return self.name

    def canOperate(self,user):
        if not user.is_active:
            return False
        if self.requires_form and not user.form_on_file:
            return False
        if not self.requires_permit:
            return True
        return self.requires_permit.hasThisPermit(user)

    def canInstruct(self,user):
        if not self.canOperate(user):
            return False
        if not self.requires_permit:
            return True
        if not self.requires_permit.permit:
            return True
        return self.requires_permit.permit(user)
        
# Special sort of create/get - where we ignore the issuer when looking for it.
# but add it in if we're creating it for the first time.
# Not sure if this is a good idea. Proly not. The other option
# would be to split entitelemtns into an entitelent and 1:N 
# endorsements.
#
# I guess we could also trap this in the one or two places wheer
# we create an Entitlement.
#
class EntitlementManager(models.Manager):
   def get_or_create(self, *args,**kwargs):
        if 'permit' in kwargs and 'holder' in kwargs:
            e = Entitlement.objects.all().filter(permit = kwargs.get('permit')).filter(holder = kwargs.get('holder'))

            if e and e.count() >= 1:
               existing = e[0]

               if e.count() > 1:
                  logger.critical("IntigrityAlert: {} identical entitlement for {}.{}".format(e.count(),kwargs.get('permit'),kwargs.get('holder')))
                  # raise DoubleEntitlemenException("Two or more indentical entitlements found. Blocking creation of a third")
               else:
                  logger.debug("Entity - trapped double create attempt: {}", existing)

               for k,v in kwargs.items():
                   setattr(existing,k,v)
               return existing, False
        return super(EntitlementManager, self).get_or_create(*args, **kwargs)

class EntitlementViolation(Exception):
        pass
class DoubleEntitlemenException(Exception):
        pass


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
    objects = EntitlementManager()

    def __str__(self):
        return str(self.holder) + '@' + self.permit.name +'(Active:'+str(self.active)+')'

    def save(self, *args, **kwargs):
        current_site = Site.objects.get(pk=settings.SITE_ID)

        user = None
        if 'request' in kwargs:
           request = kwargs['request']
           del  kwargs['request']
           current_site = get_current_site(request)
           user = request.user

        # rely on the contraints to bomb out if there is nothing in kwargs and self. and self.
        #
        if not self.issuer and user:
                  self.issuer = user
              
        issuer_permit = PermitType.objects.get(pk = self.permit.pk)

        if issuer_permit and not Entitlement.objects.filter(permit=issuer_permit,holder=self.issuer):
            if not user or not user.is_staff:
                logger.critical(f"Entitlement.save(): holder {self.issuer} cannot issue {self.permit} to {self.holder} as the holder lacks {issuer_permit}")
                raise EntitlementViolation("issuer of this entitelment lacks the entitlement to issue it.")
            logger.critical(f"Entitlement.save(): STAFFF bypass of rule 'holder {self.issuer} cannot issue {self.permit} to {self.holder} as the holder lacks {issuer_permit}'")
        if self.active == None:
            # See if we can fetch an older approval for same that may already have
            # been activated. And grandfather it in.
            try:
               e = Entitlement.objects.get(permit = self.permit, holder = self.holder);
               self.active = e.active
            except EntitlementNotFound:
                pass

        if not self.active and self.permit.permit:
            try:
                 context = { 'holder': self.holder, 
                         'issuer': self.issuer, 
                         'permit': self.permit,
                         'domain': current_site.domain,
                         }

                 subject = render_to_string('acl/notify_trustees_subject.txt', context).strip()
                 body =  render_to_string('acl/notify_trustees.txt', context)

                 EmailMessage(subject, body, 
                         to=[self.issuer.email, settings.TRUSTEES, 'dirkx@webweaving.org'], 
                         from_email=settings.DEFAULT_FROM_EMAIL
                 ).send()
            except Exception as e:
                logger.critical("Failed to sent an email: {}".format(str(e)))

        # should we check for duplicates here too ?
        #
        return super(Entitlement, self).save(*args, **kwargs)



