from django.db import models
from simple_history.models import HistoricalRecords
from members.models import User
import jsonfield
import json

def validate_json(payload):
     try:
        json.loads(payload)
     except Exception as e:
         raise ValidationError("Invalid json ({e}");

class Chore(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=200)
    class_type = models.CharField(max_length=40)
    configuration = jsonfield.JSONField(validators=[validate_json])
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='createdBy',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class ChoreVolunteer(models.Model):
    user = models.ForeignKey(
        User,
        null=False,
        on_delete=models.CASCADE,
        related_name='volunteer',
    )
    chore = models.ForeignKey(
        Chore,
        null=False,
        on_delete=models.CASCADE,
        related_name='chore',
    )
    timestamp = models.IntegerField(null=False)

    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()
