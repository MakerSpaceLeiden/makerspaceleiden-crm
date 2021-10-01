from django import template
from django.conf import settings

register = template.Library() 

@register.filter(name='has_group') 
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists() 

@register.filter(name='isMainsAdmin')
def isMainsAdmin(user):
    return user.groups.filter(name=settings.SENSOR_USER_GROUP).exists() 

@register.filter(name='isNetAdmin')
def isNetAdmin(user):
    return user.groups.filter(name=settings.NETADMIN_USER_GROUP).exists() 

@register.filter(name='isInPettycashDemGroupo')
def isInPettycashDemGroupo(user):
    return user.groups.filter(name=settings.PETTYCASH_DEMO_USER_GROUP).exists() 
