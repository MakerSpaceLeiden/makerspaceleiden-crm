from django.db import models
from members.models import User
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.conf import settings
from simple_history.models import HistoricalRecords
from django.urls import reverse_lazy, reverse


import logging

logger = logging.getLogger(__name__)


class Mailinglist(models.Model):
    name = models.CharField(
        max_length=40,
        unique=True,
        help_text="Short name; as for the '@' sign. E.g. 'spacelog'.",
    )
    description = models.CharField(max_length=400)
    mandatory = models.BooleanField(
        default=False, help_text="Requires super admin to change"
    )
    visible_months = models.IntegerField(
        default=0,
        help_text="How long these archives are visible for normal members, or blank/0 if `forever'",
    )
    hidden = models.BooleanField(
        default=False,
        help_text="Show this in the normal (non admin) view",
    )

    history = HistoricalRecords()

    def __str__(self):
        return self.name

    def path(self):
        return reverse("mailinglists_archive", kwargs={"mlist": self.name})


class Subscription(models.Model):
    mailinglist = models.ForeignKey(
        Mailinglist, on_delete=models.CASCADE, related_name="hasMember"
    )
    member = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="isSubscribedTo"
    )
    active = models.BooleanField(
        default=False, help_text="Switch off to no longer receive mail from this list."
    )
    digest = models.BooleanField(
        default=False,
        help_text="Receive all the mails of the day as one email; rather than throughout the day.",
    )
    account = None

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.member.email}@{self.mailinglist}"
