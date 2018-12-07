from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from members.models import PermitType, Member
from simple_history.models import HistoricalRecords

class Location(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description =  models.CharField(max_length=200,blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class Machine(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description =  models.CharField(max_length=200,blank=True)
    location = models.ForeignKey(Location,related_name="is_located",on_delete=models.CASCADE, blank=True, null=True)
    requires_instruction = models.BooleanField(default=False)
    requires_form = models.BooleanField(default=False)
    requires_permit = models.ForeignKey(PermitType,related_name='has_permit',on_delete=models.CASCADE, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name

class Instruction(models.Model):
    machine = models.ForeignKey(Machine,
       on_delete=models.CASCADE,
    )
    holder = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='hadInstructionFor',
    )
    issuer = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='isInstructedBy',
    )
    history = HistoricalRecords()

    def __str__(self):
        return str(self.holder) + ' had instruction on ' + self.machine.name
    def save_model(self, request, obj, form, change):
        if not obj.issuer:
            obj.issuer = request.user
        obj.save()


