from datetime import datetime, timedelta, timezone

import time_machine
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from agenda.models import Agenda, AgendaChoreStatusChange

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
        self.assertIn(self.chore.name, html)
        self.assertIn(agenda.display_datetime, html)

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


class DetailViewTests(TestCase):
    def setUp(self):
        self.password = "testpassword"
        self.user = UserFactory(password=self.password)
        self.taskCompleter = UserFactory()
        self.client = Client()
        self.chore = Chore.objects.create(
            name="Test Chore Detail",
            description="A test chore for detail view.",
            class_type="BasicChore",
            configuration={"foo": "bar"},
            creator=self.user,
        )

    def test_detail_requires_auth(self):
        url = reverse("chore_detail", kwargs={"pk": self.chore.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    @time_machine.travel("2025-05-10 14:56")
    def test_detail_view_renders_agenda_and_status(self):
        self.agenda = Agenda.objects.create(
            startdatetime=datetime.now(tz=timezone.utc) - timedelta(days=2),
            enddatetime=datetime.now(tz=timezone.utc) + timedelta(days=1),
            item_title="Agenda for Chore Detail",
            item_details="Agenda details.",
            user=self.user,
            chore=self.chore,
            status="completed",
        )
        # Add two status changes, only the most recent completed should be loaded
        AgendaChoreStatusChange.objects.create(
            agenda=self.agenda,
            user=self.user,
            status="in_progress",
        )
        self.completed_status = AgendaChoreStatusChange.objects.create(
            agenda=self.agenda,
            user=self.taskCompleter,
            status="completed",
        )

        self.assertTrue(
            self.client.login(email=self.user.email, password=self.password)
        )
        url = reverse("chore_detail", kwargs={"pk": self.chore.pk})
        response = self.client.get(url)
        html = response.content.decode("utf-8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agenda item should be present
        self.assertIn("Sat 2025-05-10 14:56:00", html)
        # Most recent completed status change should be present
        self.assertIn(self.completed_status.status, html)
        # The user who completed should be present
        self.assertIn(str(self.completed_status.user), html)

    @time_machine.travel("2025-05-10 14:56")
    def test_detail_view_renders_agenda_with_cta(self):
        self.agenda = Agenda.objects.create(
            startdatetime=datetime.now(tz=timezone.utc) - timedelta(days=2),
            enddatetime=datetime.now(tz=timezone.utc) + timedelta(days=1),
            item_title="Agenda for Chore Detail",
            item_details="Agenda details.",
            user=self.user,
            chore=self.chore,
        )

        self.assertTrue(
            self.client.login(email=self.user.email, password=self.password)
        )
        url = reverse("chore_detail", kwargs={"pk": self.chore.pk})
        response = self.client.get(url)
        html = response.content.decode("utf-8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agenda item should be present
        self.assertIn('data-test-hook="mark-chore-as-completed"', html)
