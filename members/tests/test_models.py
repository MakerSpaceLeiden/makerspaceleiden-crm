from django.utils import timezone
from datetime import datetime
from chores.tests.factories import UserFactory
from django.test import TestCase
from acl.models import Location

class MembersModelsTest(TestCase):
    def setUp(self):
        self.user = UserFactory(
            email="member.author@example.com",
        )

        self.location = Location.objects.create(name="Test Location")

    def test_member_checkin(self):
        self.user.checkin()
        self.assertEqual(self.user.is_onsite, True)


    def test_member_checkin_with_location_id(self):
        self.user.checkin(
            location=self.location,
        )
        self.assertEqual(self.user.is_onsite, True)
        self.assertEqual(self.user.location.id, self.location.id)

    def test_member_checkout(self):
        self.user.checkout()
        self.assertEqual(self.user.is_onsite, False)

    def test_member_checkout_with_location_id(self):
        self.user.checkout(
            location=self.location,
        )
        self.assertEqual(self.user.is_onsite, False)
        self.assertEqual(self.user.location, None)