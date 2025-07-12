import json

import jsonfield
from django.core import exceptions
from django.db import models
from simple_history.models import HistoricalRecords

from members.models import User


def validate_json(payload):
    return
    try:
        json.loads(payload)
    except Exception as e:
        raise exceptions.ValidationError("Invalid json {}".format(e))


class Chore(models.Model):
    name = models.CharField(max_length=40, unique=True)
    description = models.CharField(max_length=200)
    class_type = models.CharField(max_length=40)
    configuration = jsonfield.JSONField(validators=[validate_json])
    wiki_url = models.URLField(blank=True, null=True)
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="createdBy",
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
        related_name="volunteer",
    )
    chore = models.ForeignKey(
        Chore,
        null=False,
        on_delete=models.CASCADE,
        related_name="chore",
    )

    # Represents when the chore is scheduled to begin
    timestamp = models.IntegerField(null=False)

    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"


class ChoreNotification(models.Model):
    event_key = models.CharField(max_length=128, unique=True)
    chore = models.ForeignKey(
        Chore,
        null=False,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    recipient_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chore_notifications",
    )

    recipient_other = models.EmailField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.recipient_user and not self.recipient_other:
            raise ValidationError(
                "Must have either a recipient_user or a recipient_other."
            )
        if self.recipient_user and self.recipient_other:
            raise ValidationError(
                "Cannot have both recipient_user and recipient_other."
            )

    def __str__(self):
        recipient = self.recipient_user if self.recipient_user else self.recipient_other
        return f"Notification to {recipient} for {self.chore} at {self.created_at}"
