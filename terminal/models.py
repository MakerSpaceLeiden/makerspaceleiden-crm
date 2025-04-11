import logging
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from simple_history.models import HistoricalRecords

from makerspaceleiden.mail import emailPlain
from members.models import User

logger = logging.getLogger(__name__)


def terminal_admin_emails():
    return list(
        User.objects.all()
        .filter(groups__name=settings.PETTYCASH_ADMIN_GROUP)
        .values_list("email", flat=True)
    )


class Terminal(models.Model):
    name = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Name, initially as reported by the firmware. Potentially not unique!",
    )
    fingerprint = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="SHA256 fingerprint of the client certificate.",
    )
    nonce = models.CharField(
        max_length=64, blank=True, null=True, help_text="256 bit nonce (as HEX)"
    )
    date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Time and date the device was last seen",
        auto_now_add=True,
    )
    accepted = models.BooleanField(
        default=False,
        help_text="Wether an administrator has checked the fingerprint against the display on the device and accepted it manually; or implictly by swiping their tag at the actual device. Unsetting this flags blocks the terminal from interacting with teh payment and authorisation system. But will not wipe its (authorisation) cache.",
    )
    history = HistoricalRecords()

    def __str__(self):
        return "%s@%s %s...%s" % (
            self.name,
            self.date.strftime("%Y/%m/%d %H:%M"),
            self.fingerprint[:4],
            self.fingerprint[-4:],
        )

    def save(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(
            minutes=settings.PETTYCASH_TERMS_MINS_CUTOFF
        )

        # Drop anything that is too old; and only keep the most recent up to
        # a cap -- feeble attempt at foiling obvious DOS. Mainly as the tags
        # can be as short as 32 bits and we did not want to also add a shared
        # scecret in the Arduino code. As these easily get committed to github
        # by accident.
        stale = Terminal.objects.all().filter(Q(accepted=False)).order_by("date")
        if len(stale) > settings.PETTYCASH_TERMS_MAX_UNKNOWN:
            lst = (
                User.objects.all()
                .filter(groups__name=settings.PETTYCASH_ADMIN_GROUP)
                .values_list("email", flat=True)
            )
            emailPlain(
                "pettycash-dos-warn.txt",
                toinform=lst,
                context={"base": settings.BASE, "settings": settings, "stale": stale},
            )
            logger.info("DOS mail set about too many terminals in waiting.")
        todel = set()
        for s in stale.filter(Q(date__lt=cutoff)):
            todel.add(s)
        for s in stale[settings.PETTYCASH_TERMS_MIN_UNKNOWN :]:
            todel.add(s)
        for s in todel:
            s.delete()

        return super(Terminal, self).save(*args, **kwargs)
