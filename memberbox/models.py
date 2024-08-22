import logging

from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from simple_history.models import HistoricalRecords
from stdimage.models import StdImageField

from makerspaceleiden.mail import emailPlain, emails_for_group
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

    # Return the relative path of this member (we do not
    # yet have a page for the box(es) of a member.
    #
    def url(self):
        return reverse("overview", kwargs={"member_id": self.id})

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

    def can_delete(user):
        if self.owner == user:
            return True
        if user.is_privileged:
            return True
        return user.in_group(settings.MEMBERBOX_ADMIN_GROUP)

    def delete(self, user, save=True):
        if not self.can_delete(user):
            logger.critical(
                "User {} tried to delete box {} owned by {}. Denied".format(
                    user, self, self.owner
                )
            )
            raise Exception("Access denied")

        dst = self.owner.email
        context = {
            "email": self.owner.email,
            "owner": self.owner.first_name + " " + self.owner.last_name,
            "location": self.location,
            "user": user,
        }
        try:
            body = render_to_string("memberbox/email_delete.txt", context)
            subject = render_to_string(
                "memberbox/email_delete_subject.txt", context
            ).strip()

            admins = emails_for_group(settings.MEMBERBOX_ADMIN_GROUP)
            if admins:
                context["admins"] = admins
                dst.append(admins)
            else:
                dst.append(settings.TRUSTEES)

            emailPlain("memberbox/email_delete.txt", toinform=dst, context=context)
        except Exception as e:
            logger.critical(
                "Failed to sent 'empty your storage box' email: {}".format(str(e))
            )

        super(Memberbox, self).delete()


# Handle image cleanup.
# pre_delete.connect(pre_delete_delete_callback, sender=Memberbox)
# pre_save.connect(pre_save_delete_callback, sender=Memberbox)
