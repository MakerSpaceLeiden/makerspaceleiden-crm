from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

# Create your models here.
class Member(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
	default='',
    )
    form_on_file = models.BooleanField( 
	default=False,
    )
    def __str__(self):
        return self.user.username

class Tag(models.Model):
    owner = models.ForeignKey(Member, on_delete=models.CASCADE)
    tag = models.CharField(max_length=30)
    def __str__(self):
        return self.tag + ' (' + self.owner.user.username + ')'

class PermitType(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description =  models.CharField(max_length=200)
    def __str__(self):
        return self.name

class Entitlement(models.Model):
    permit = models.ForeignKey(
	'PermitType',
	on_delete=models.CASCADE,
    )
    holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='isGivenTo',
    )
    issuer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='isIssuedBy',
    )
    def __str__(self):
        return str(self.holder) + ' on ' + self.permit.name
    def save_model(self, request, obj, form, change):
        if not obj.issuer:
            obj.issuer = request.user
        obj.save()

