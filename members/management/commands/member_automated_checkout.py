import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from members.models import User

logger = logging.getLogger(__name__)

MAX_HOURS_BEFORE_STALE = 8
MEMBER_AUTOMATED_CHECKOUT_EMAIL_SUBJECT = "Your account has been checked out"


class Command(BaseCommand):
    help = "Automated checkout of members"

    def handle(self, *args, **options):
        """Checkouts members who have been checked in for more than configured maximum hours"""
        logger.info("checkout members")
        checked_in = User.objects.filter(
            is_onsite=True,
            onsite_updated_at__lte=timezone.now()
            - timedelta(hours=MAX_HOURS_BEFORE_STALE),
        )

        if len(checked_in) == 0:
            self.stdout.write("No users to check out")
            return

        logger.info(f"checkout members: {len(checked_in)}")

        for u in checked_in:
            try:
                with transaction.atomic():
                    u.checkout()
                    EmailMessage(
                        subject=MEMBER_AUTOMATED_CHECKOUT_EMAIL_SUBJECT,
                        body=render_to_string(
                            "members/email_checkout.txt",
                            {
                                "user": u,
                                "url_space_state": settings.BASE
                                + reverse("space_state"),
                                "url_notification_settings": settings.BASE
                                + reverse("notification_settings"),
                            },
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[u.email],
                    ).send()
                    self.stdout.write(f"Checked out {u.email}")
            except Exception as e:
                self.stderr.write(f"Failed for {u.email}: {e}")
