import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import render_to_string
from simple_history.models import HistoricalRecords
from stdimage.models import StdImageField

from makerspaceleiden.utils import upload_to_pattern
from members.models import User

logger = logging.getLogger(__name__)


class Memberbox(models.Model):
    image = StdImageField(
        upload_to=upload_to_pattern,
        blank=True,
        null=True,
        delete_orphans=True,
        variations=settings.IMG_VARIATIONS,
        validators=settings.IMG_VALIDATORS,
        help_text="Optional - but highly recommened.",
    )

    location = models.CharField(
        max_length=40,
        unique=True,
        help_text="Use left/right - shelf (top=1) - postion. E.g. R24 is the right set of shelves, second bin on the 4th row from the bottom. Or use any other descriptive string (e.g. 'behind the bandsaw')",
    )
    extra_info = models.CharField(
        max_length=200,
        help_text="Such as 'plastic bin'. Especially important if you are keeping things in an odd place.",
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    history = HistoricalRecords()

    def url(self):
        return settings.BASE + self.path()

    def __str__(self):
        if self.owner:
            return (
                "Box owned by "
                + self.owner.first_name
                + " "
                + self.owner.last_name
                + " at "
                + self.location
            )
        return "Box at " + self.location + " (owner unknown)"

    def delete(self, save=True):
        context = {
            "email": self.owner.email,
            "owner": self.owner.first_name + " " + self.owner.last_name,
            "location": self.location,
        }
        try:
            body = render_to_string("memberbox/email_delete.txt", context)
            subject = render_to_string(
                "memberbox/email_delete_subject.txt", context
            ).strip()

            EmailMessage(
                subject,
                body,
                to=[context["email"], settings.TRUSTEES, "dirkx@webweaving.org"],
                from_email=settings.DEFAULT_FROM_EMAIL,
            ).send()
        except Exception as e:
            logger.critical(
                "Failed to sent empty your storage box email: {}".format(str(e))
            )

        super(Memberbox, self).delete()


# Handle image cleanup.
# pre_delete.connect(pre_delete_delete_callback, sender=Memberbox)
# pre_save.connect(pre_save_delete_callback, sender=Memberbox)
