from datetime import datetime, timedelta, timezone

from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from agenda.models import Agenda

from ..models import Chore
from .factories import UserFactory


class IndexViewTests(TestCase):
    def setUp(self):
        self.password = "testpassword"
        self.user = UserFactory(password=self.password)
        self.client = Client()
        self.chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore that needs volunteers.",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 1,
                },
                "reminders": [],
            },
            creator=self.user,
        )

    def test_index_root_path_returns_200(self):
        # If the root path is named 'chores', use reverse; otherwise, use '/'
        self.assertTrue(
            self.client.login(email=self.user.email, password=self.password)
        )

        agenda = Agenda.objects.create(
            startdatetime=datetime.now(tz=timezone.utc) + timedelta(days=2),
            enddatetime=datetime.now(tz=timezone.utc) + timedelta(days=3),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
            chore=self.chore,
        )

        try:
            url = reverse("chores")
        except Exception:
            url = "/"
        response = self.client.get(url)
        html = response.content.decode("utf-8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(agenda.item_details, html)

    def test_api_path_returns_200(self):
        # If the root path is named 'chores', use reverse; otherwise, use '/'
        self.assertTrue(
            self.client.login(email=self.user.email, password=self.password)
        )

        Agenda.objects.create(
            startdatetime=datetime.now(tz=timezone.utc) + timedelta(days=2),
            enddatetime=datetime.now(tz=timezone.utc) + timedelta(days=3),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
            chore=self.chore,
        )

        try:
            url = reverse("chores_api")
        except Exception:
            url = "/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
