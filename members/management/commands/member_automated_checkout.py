from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from members.models import User

MAX_HOURS_BEFORE_STALE = 8

MEMBER_AUTOMATED_CHECKOUT_EMAIL_SUBJECT = "Your account has been checked out"


class Command(BaseCommand):
    help = "Automated checkout of members"

    def handle(self, *args, **options):
        """Checkouts members who have been checked in for more than configured maximum hours"""
        checked_in = User.objects.filter(
            is_onsite=True,
            onsite_updated_at__lte=datetime.now(timezone.utc)
            - timedelta(hours=MAX_HOURS_BEFORE_STALE),
        )

        for u in checked_in:
            u.checkout()
            send_mail(
                MEMBER_AUTOMATED_CHECKOUT_EMAIL_SUBJECT,
                render_to_string(
                    "members/email_checkout.txt",
                    {
                        "user": u,
                        "url_space_state": reverse("space_state"),
                        "url_notification_settings": reverse("notification_settings"),
                    },
                ),
                settings.DEFAULT_FROM_EMAIL,
                [u.email],
                fail_silently=False,
            )
