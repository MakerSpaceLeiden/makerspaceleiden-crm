import json

import time_machine
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework import status

from ..models import Chore, ChoreVolunteer
from .factories import UserFactory

fake = Faker()

User = get_user_model()


# Load the schema from a file
def load_schema(schema_path):
    with open(schema_path, "r") as schema_file:
        return json.load(schema_file)


class ChoresViewsTest(TestCase):
    def setUp(self):
        self.user = UserFactory(password="testpassword")

    @time_machine.travel("2025-07-13 14:56")
    def create_chore(self, **kwargs):
        defaults = dict(
            name=fake.name(),
            description="A test chore that needs volunteers.",
            class_type="BasicChore",
            wiki_url=fake.url(),
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [],
            },
            creator=self.user,
        )
        defaults.update(kwargs)
        return Chore.objects.create(**defaults)

    @time_machine.travel("2025-07-13 14:56")
    def test_empty_chores_overview_200(self):
        """Test that the empty chores overview returns a 200 response"""
        url = reverse("chores")
        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data-test-hook="empty-chores"', response.content.decode("utf-8"))

    @time_machine.travel("2025-07-13 14:56")
    def test_chores_overview_with_chore_200(self):
        url = reverse("chores")
        chore = self.create_chore()

        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)
        response = self.client.get(url)
        html = response.content.decode("utf-8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(chore.description, html)
        self.assertIn('data-test-hook="chores-volunteer-button"', html)
        self.assertNotIn('data-test-hook="chores-volunteer"', html)
        self.assertNotIn('data-test-hook="empty-chores"', html)

    @time_machine.travel("2025-07-13 14:56")
    def test_chores_overview_with_chore_and_volunteer_200(self):
        url = reverse("chores")
        chore = self.create_chore()
        volunteer = UserFactory()
        ChoreVolunteer.objects.create(user=volunteer, chore=chore, timestamp=1753041600)

        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)
        response = self.client.get(url)
        html = response.content.decode("utf-8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(chore.description, html)
        self.assertIn('data-test-hook="chores-volunteer"', html)
        self.assertIn(volunteer.first_name, html)
        self.assertNotIn('data-test-hook="empty-chores"', html)

    @time_machine.travel("2025-07-13 14:56")
    def test_signup_success(self):
        chore = self.create_chore()
        ts = 1753041600
        url = reverse("signup_chore", args=[chore.id, ts])
        self.client.login(email=self.user.email, password="testpassword")
        response = self.client.get(url + "?redirect_to=chores")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("chores", response.url)
        self.assertTrue(
            ChoreVolunteer.objects.filter(
                user=self.user, chore=chore, timestamp=ts
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("volunteer", mail.outbox[0].body)

    @time_machine.travel("2025-07-13 14:56")
    def test_signup_chore_not_found(self):
        self.client.login(email=self.user.email, password="testpassword")
        url = reverse("signup_chore", args=[9999, 1753041600])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Chore not found", response.content.decode())

    @time_machine.travel("2025-07-13 14:56")
    def test_signup_double(self):
        chore = self.create_chore()
        ts = 1753041600
        ChoreVolunteer.objects.create(user=self.user, chore=chore, timestamp=ts)
        self.client.login(email=self.user.email, password="testpassword")
        url = reverse("signup_chore", args=[chore.id, ts])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        # Should not create duplicate
        self.assertEqual(
            ChoreVolunteer.objects.filter(
                user=self.user, chore=chore, timestamp=ts
            ).count(),
            2,
        )

    @time_machine.travel("2025-07-13 14:56")
    def test_signup_requires_login(self):
        chore = self.create_chore()
        ts = 1753041600
        url = reverse("signup_chore", args=[chore.id, ts])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/login/", response.url)

    @time_machine.travel("2025-07-13 14:56")
    def test_remove_signup_success(self):
        chore = self.create_chore()
        ts = 1753041600
        ChoreVolunteer.objects.create(user=self.user, chore=chore, timestamp=ts)
        self.client.login(email=self.user.email, password="testpassword")
        url = reverse("remove_signup_chore", args=[chore.id, ts])
        response = self.client.get(url + "?redirect_to=chores")
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/chores", response.url)
        self.assertFalse(
            ChoreVolunteer.objects.filter(
                user=self.user, chore=chore, timestamp=ts
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("can no longer volunteer", mail.outbox[0].body)

    @time_machine.travel("2025-07-13 14:56")
    def test_remove_signup_chore_not_found(self):
        self.client.login(email=self.user.email, password="testpassword")
        url = reverse("remove_signup_chore", args=[9999, 1753041600])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Chore not found", response.content.decode())

    @time_machine.travel("2025-07-13 14:56")
    def test_remove_signup_not_signed_up(self):
        chore = self.create_chore()
        ts = 1753041600
        self.client.login(email=self.user.email, password="testpassword")
        url = reverse("remove_signup_chore", args=[chore.id, ts])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertFalse(
            ChoreVolunteer.objects.filter(
                user=self.user, chore=chore, timestamp=ts
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("can no longer volunteer", mail.outbox[0].body)

    @time_machine.travel("2025-07-13 14:56")
    def test_remove_signup_requires_login(self):
        chore = self.create_chore()
        ts = 1753041600
        url = reverse("remove_signup_chore", args=[chore.id, ts])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("login/", response.url)

    @time_machine.travel("2025-07-13 14:56")
    def test_index_requires_login(self):
        url = reverse("chores")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("/login/", response.url)

    @time_machine.travel("2025-07-13 14:56")
    def test_remove_me_as_volunteer_button_visible_for_volunteer(self):
        """Test that the 'Remove me as volunteer' button is visible for the logged-in user who volunteered."""
        chore = self.create_chore()
        ts = 1753041600
        # The logged-in user volunteers for the chore
        ChoreVolunteer.objects.create(user=self.user, chore=chore, timestamp=ts)
        self.client.login(email=self.user.email, password="testpassword")
        url = reverse("chores")
        response = self.client.get(url)
        html = response.content.decode("utf-8")
        self.assertIn('data-test-hook="chores-remove-volunteer"', html)
