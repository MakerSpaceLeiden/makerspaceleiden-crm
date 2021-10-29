from django import template
from django.conf import settings
from pettycash.models import PettycashBalanceCache 


register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name="isMainsAdmin")
def isMainsAdmin(user):
    return user.groups.filter(name=settings.SENSOR_USER_GROUP).exists()


@register.filter(name="isNetAdmin")
def isNetAdmin(user):
    return user.groups.filter(name=settings.NETADMIN_USER_GROUP).exists()


@register.filter(name="isInPettycashDemGroupo")
def isInPettycashDemGroupo(user):

    if 'PETTYCASH_DEMO_USER_GROUP' in globals():
         return user.groups.filter(name=settings.PETTYCASH_DEMO_USER_GROUP).exists()

    # check if non-zero balance or if there was a transaction 
    # in last PETTYCASH_NOUSE_DAYS days
    #
    try:
          b=PettycashBalanceCache.objects.get(owner = user)
          if b.balance.amount != 0:
                return True

          cutoff = datetime.now(tz=timezone.utc) - settings.PETTYCASH_NOUSE_DAYS
          if b.date > cutoff:
                return True

    except ObjectDoesNotExist as e:
          pass

    return False
