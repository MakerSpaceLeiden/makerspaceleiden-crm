from django.conf import settings
from django.db import models
from django.urls import reverse
from stdimage.models import StdImageField

from acl.models import Machine
from makerspaceleiden.utils import upload_to_pattern
from members.models import User


class Servicelog(models.Model):
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
        return reverse("service_log_view", kwargs={"machine_id": self.machine.id})


# Handle image cleanup.
