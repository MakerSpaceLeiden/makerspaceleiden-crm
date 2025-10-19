from datetime import datetime, timezone

import time_machine
from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from chores.tests.factories import UserFactory
from members.management.commands.member_automated_checkout import (
    MEMBER_AUTOMATED_CHECKOUT_EMAIL_SUBJECT,
)


class MembersAutomatedCheckoutTest(TestCase):
    def setUp(self):
        self.user = UserFactory(
            email="member.author@example.com",
            is_onsite=True,
            onsite_updated_at=datetime(2025, 7, 14, 20, 00, 0, 0, tzinfo=timezone.utc),
        )

        self.stale_user = UserFactory(
            email="stale.user@example.com",
            is_onsite=True,
            onsite_updated_at=datetime(2025, 7, 14, 13, 00, 0, 0, tzinfo=timezone.utc),
        )

    @time_machine.travel("2025-07-15 00:00")
    def test_member_automated_checkout(self):
        call_command("member_automated_checkout")

        self.user.refresh_from_db()
        self.stale_user.refresh_from_db()

        self.assertEqual(self.user.is_onsite, True)
        self.assertEqual(self.stale_user.is_onsite, False)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, MEMBER_AUTOMATED_CHECKOUT_EMAIL_SUBJECT
        )
        self.assertEqual(mail.outbox[0].to, [self.stale_user.email])
