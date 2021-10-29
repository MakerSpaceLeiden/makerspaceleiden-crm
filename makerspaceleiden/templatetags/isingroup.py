from django import template
from django.conf import settings
from pettycash.models import PettycashBalanceCache
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from datetime import datetime, timedelta

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


@register.filter(name="isPettycashUser")
def isPettycashUser(user):
    if "PETTYCASH_DEMO_USER_GROUP" in globals():
        return user.groups.filter(name=settings.PETTYCASH_DEMO_USER_GROUP).exists()

    # check if non-zero balance or if there was a transaction
    # in last PETTYCASH_NOUSE_DAYS days
    #
    try:
        b = PettycashBalanceCache.objects.get(owner=user)
        if b.balance.amount != 0:
            return True

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days = settings.PETTYCASH_NOUSE_DAYS)
        if b.last and b.last.date > cutoff:
            return True

    except ObjectDoesNotExist as e:
        pass

    return False


@register.filter(name="isPettycashAdmin")
def isInPettycashAdmin(user):
    if user.is_privileged:
        return True
    
    return user.groups.filter(name=settings.PETTYCASH_ADMIN_GROUP).exists()
