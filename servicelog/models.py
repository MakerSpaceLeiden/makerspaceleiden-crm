from django.db import models

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from acl.models import Machine
from members.models import User

from django.conf import settings

from stdimage.models import StdImageField
from stdimage.validators import MinSizeValidator, MaxSizeValidator
from django.urls import reverse

from makerspaceleiden.utils import upload_to_pattern


from django.db.models.signals import pre_delete, pre_save

# from stdimage.utils import pre_delete_delete_callback, pre_save_delete_callback

import re


class Servicelog(models.Model):
    # UNKNOWN = 'UKNOWN'
    FOUND_BROKEN = "FOUND_BROKEN"
    FOUND_FIX_BROKEN = "FOUND_FIX_BROKEN"
    BROKEN = "BROKEN"
    BROKEN_FIXED = "BROKEN_FIXED"
    OTHER = "OTHER"
    FIXED = "FIXED"

    CAUSES = (
        (FOUND_BROKEN, "I found it already in this state"),
        (FOUND_FIX_BROKEN, "I found it in this state, and fixed/cleaned it"),
        (BROKEN, "I accidentally broke it and need help fixing it"),
        (BROKEN_FIXED, "I accidentally broke it and fixed it"),
        (OTHER, "Other - describe the situation in the descrition field"),
        (FIXED, "Checked and put back in operation"),
    )

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)

    reporter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="isReportedBy"
    )
    reported = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    description = models.TextField(max_length=16 * 1024)

    image = StdImageField(
        delete_orphans=True,
        upload_to=upload_to_pattern,
        blank=True,
        variations=settings.IMG_VARIATIONS,
        validators=settings.IMG_VALIDATORS,
        help_text="Upload an image; if relevant - optional. Fine to leave blank, upload later or post someting later to the mailing list",
    )

    situation = models.CharField(
        max_length=20, choices=CAUSES, default=BROKEN, blank=False, null=True
    )

    def url(self):
        return settings.BASE + self.path()

    def path(self):
        return reverse("service_log_view", kwargs={"machine_id": self.id})


# Handle image cleanup.
# pre_delete.connect(pre_delete_delete_callback, sender=Servicelog)
# pre_save.connect(pre_save_delete_callback, sender=Servicelog)
