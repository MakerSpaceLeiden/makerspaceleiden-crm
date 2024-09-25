import datetime
import logging

from django.conf import settings
from django.db import models
from django.urls import reverse

# frmm django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from stdimage.models import StdImageField

from makerspaceleiden.utils import upload_to_pattern
from members.models import User

# from stdimage.utils import pre_delete_delete_callback, pre_save_delete_callback


logger = logging.getLogger(__name__)


class Ufo(models.Model):
    UFO_STATE = (
        ("UNK", "Unidentified"),
        ("OK", "Claimed"),
        ("DEL", "can be disposed"),
        ("DON", "Donated to the space"),
        ("GONE", "Gone"),
    )
    image = StdImageField(
        upload_to=upload_to_pattern,
        delete_orphans=True,
        variations=settings.IMG_VARIATIONS,
        validators=settings.IMG_VALIDATORS,
    )
    description = models.CharField(max_length=300, blank=True, null=True)

    state = models.CharField(
        max_length=4, choices=UFO_STATE, default="UNK", blank=True, null=True
    )

    deadline = models.DateField(blank=True, null=True)
    dispose_by_date = models.DateField(blank=True, null=True)

    lastChange = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    claimed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="claimed_ufos",
    )
    claimed_at = models.DateTimeField(blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    history = HistoricalRecords()

    def url(self):
        return settings.BASE + self.path()

    def path(self):
        return reverse("showufo", kwargs={"pk": self.id})

    def __str__(self):
        return self.description

    def save(self, *args, **kwargs):
        self.lastChange = datetime.date.today()

        if not self.deadline:
            self.deadline = datetime.date.today() + datetime.timedelta(
                settings.UFO_DEADLINE_DAYS
            )

        if not self.dispose_by_date:
            self.dispose_by_date = self.deadline + datetime.timedelta(
                settings.UFO_DISPOSE_DAYS
            )

        if self.dispose_by_date < self.deadline:
            self.dispose_by_date = self.deadline + datetime.timedelta(1)

        return super(Ufo, self).save(*args, **kwargs)


# Handle image cleanup.
# pre_delete.connect(pre_delete_delete_callback, sender=Ufo)
# pre_save.connect(pre_save_delete_callback, sender=Ufo)
