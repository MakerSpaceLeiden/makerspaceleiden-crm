from django.db import models
from members.models import User
from django.db.models.signals import post_delete,post_save, pre_delete, pre_save
from django.conf import settings
from simple_history.models import HistoricalRecords
from django.urls import reverse_lazy,reverse


import logging
logger = logging.getLogger(__name__)

from .mailman import MailmanService, MailmanAccount
service = MailmanService(settings.ML_PASSWORD, settings.ML_ADMINURL)

class Mailinglist(models.Model):
    name = models.CharField(max_length=40, unique=True, help_text = "Short name; as for the '@' sign. E.g. 'spacelog'.")
    description =  models.CharField(max_length=400)
    mandatory = models.BooleanField(default=False,help_text = 'Requires super admin to change')

    visible_months = models.IntegerField(default=0, help_text="How long these archives are visible for normal members, or blank/0 if `forever'")

    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def path(self):
        return reverse('mailinglists_archive', kwargs = { 'mlist': self.name  })

class Subscription(models.Model):
    mailinglist = models.ForeignKey(Mailinglist, on_delete=models.CASCADE, related_name='hasMember')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='isSubscribedTo')
    active = models.BooleanField(default=False,help_text="Switch off to no longer receive mail from this list.")
    digest = models.BooleanField(default=False, help_text="Receive all the mails of the day as one email; rather than throughout the day.")
    account = None

    history = HistoricalRecords()

    def __str__(self):
        return f'{self.member.email} @ {self.mailinglist}'

    def manage(self,subscribe):
        # Sync (un)subscribe
        pass

    # Sync active bit and REST setings admin tool.
    #
    def sync_activate(self):
        # Force subscribe if needed ?
        #
        # if not self.account.is_subscribed:
        #     self.subscribe(True)
        #
        if not self.account:
              self.account = MailmanAccount(service, self.mailinglist)
        email = self.member.email

        self.account.digest(email, self.digest)
        self.account.delivery(email, self.active)

        # if active != self.active or digest != self.digest:
        #    raise Exception("out of sync with server.")

    def subscribe(self):
        if not self.account:
              self.account = MailmanAccount(service, self.mailinglist)

        self.account.subscribe(self.member.email, self.member.name())

    def unsubscribe(self):
        if not self.account:
              self.account = MailmanAccount(service, self.mailinglist)
        self.account.unsubscribe(self.member.email)

def sub_deleted(sender,instance,**kwargs):
     instance.unsubscribe()

def sub_saved(sender, instance, created, **kwars):
     if created:
        instance.subscribe()
     instance.sync_activate()

def user_saved(sender, instance, created, **kwargs):
     if created:
         for mailinglist in Mailinglist.objects.all():
             sub = Subscription(mailinglist = mailinglist, member = sender, active = False)
             sub.changeReason("Create triggered by user save")
             sub.save()
 
     # for sub in Subscription.objects.all().filter(member = instance):
     #    sub.manage(instance.is_active)

post_delete.connect(sub_deleted, sender=Subscription)

post_save.connect(user_saved, sender=User.is_active)
post_save.connect(sub_saved, sender=Subscription)

