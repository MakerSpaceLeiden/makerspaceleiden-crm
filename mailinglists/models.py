from django.db import models
from members.models import User
from django.db.models.signals import post_delete,post_save, pre_delete, pre_save

class Maillinglist(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description =  models.CharField(max_length=400)

class Mailinglist_subscription(models.Model):
    maillinglist = models.ForeignKey(Maillinglist, n_delete=models.CASCADE, related_name='hasMember')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='isSubscribedTo')
    active = models.BooleanField(default=False)

    mandatory = models.BooleanField(default=False,help_text = 'Requires super admin to change')

    ''' 
    subscribe [password] [digest|nodigest] [address=<address>]
       Subscribe to this mailing list.  Your password must be given to
       unsubscribe or change your options, but if you omit the password, one
       will be generated for you.  You may be periodically reminded of your
       password.

       The next argument may be either: `nodigest' or `digest' (no quotes!).
       If you wish to subscribe an address other than the address you sent
       this request from, you may specify `address=<address>' (no brackets
       around the email address, and no quotes!)

    unsubscribe [password] [address=<address>]
       Unsubscribe from the mailing list.  If given, your password must match
       your current password.  If omitted, a confirmation email will be sent
       to the unsubscribing address. If you wish to unsubscribe an address
       other than the address you sent this request from, you may specify
       `address=<address>' (no brackets around the email address, and no
       quotes!)

    '''
    def manage(self,subscribe):
        # Sync (un)subscribe
        pass

    def sync_activate(self):
        # Sync active bit and REST setings admin tool
        pass
    def subscribe(self):
        self.manage(True)

    def unsubscribe(self):
        self.manage(False)

def sub_delete(sender,instance,using):
     instance.unsubscribe()

def sub_saved(sender,instance,created,raw,using,update_fields):
     if created:
        instance.subscribe()
     instance.sync_activate()

def user_delete(sender,instance,using):
     # Delete all this users subscriptions.
     for sub in Mailinglist_subscription.objects.all().filter(member = instace):
         sub.delete()

def user_saved(sender,instance,created,raw,using,update_fields):
     if created:
         for mailinglist in Mailinglist.objects.all():
             sub = Mailinglist_subscription(mailinglist = mailinglist, member = sender, active = False)
             sub.changeReason("Create triggered by user save")
             sub.save()
 
     for sub in Mailinglist_subscription.objects.all().filter(member = instance).exclude(active = instance.active)
         sub.manage(instance.active)

pre_save.connect(user_changed, sender=User.active)
pre_save.connect(sub_changed, sender=Mailinglist_subscription)

post_delete.connect(user_delete, sender=User)
post_delete.connect(sub_delete, sender=Mailinglist_subscription)
