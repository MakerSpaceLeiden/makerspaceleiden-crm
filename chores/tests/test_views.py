from datetime import datetime, timedelta, timezone

import time_machine
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status

from acl.models import User
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

    @time_machine.travel("2025-05-10 14:56")
    def test_detail_view_renders_futuer_agenda_item_without_cta(self):
        self.agenda = Agenda.objects.create(
            startdatetime=datetime.now(tz=timezone.utc) + timedelta(days=20),
            enddatetime=datetime.now(tz=timezone.utc) + timedelta(days=21),
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
        self.assertNotIn('data-test-hook="mark-chore-as-completed"', html)


class CreateChoreTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="example@example.com",
        )
        permission = Permission.objects.get(
            codename="add_chore", content_type=ContentType.objects.get_for_model(Chore)
        )
        self.user.user_permissions.add(permission)

        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)

    def test_create_chore_get_requires_permission(self):
        url = reverse("chore_create")

        user_no_permission = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="no_permission@example.com",
        )

        self.assertTrue(
            self.client.login(email=user_no_permission.email, password="testpassword")
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_chore_get(self):
        url = reverse("chore_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "chores/chore_crud.html")

    def test_create_chore_post(self):
        url = reverse("chore_create")
        starting_from = "2025-05-10 14:56"
        response = self.client.post(
            url,
            {
                "name": "Test Chore",
                "description": "A test chore that needs volunteers.",
                "wiki_url": "https://example.com",
                "frequency": 23,
                "starting_from": starting_from,
                "cron": "0 22 * * mon",
                "duration_value": 1,
                "duration_unit": "w",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        chore = Chore.objects.get(name="Test Chore")
        self.assertEqual(chore.description, "A test chore that needs volunteers.")
        self.assertEqual(chore.wiki_url, "https://example.com")
        self.assertTemplateUsed(response, "chores/chore_detail.html")
        self.assertEqual(
            {
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "2025/05/10 14:56",
                    "crontab": "0 22 * * mon",
                    "take_one_every": 23,
                    "duration": "P7D",
                },
            },
            chore.configuration,
        )
        self.assertIn('data-test-hook="success"', response.content.decode("utf-8"))


class UpdateChoreTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="example@example.com",
        )
        permission = Permission.objects.get(
            codename="change_chore",
            content_type=ContentType.objects.get_for_model(Chore),
        )
        self.user.user_permissions.add(permission)

        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)

        self.user_no_permission = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="no_permission@example.com",
        )

        self.chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore that needs volunteers.",
            class_type="BasicChore",
            configuration={
                "events_generation": {
                    "event_type": "recurrent",
                    "take_one_every": 233,
                    "starting_time": "2025/05/10 14:56",
                    "crontab": "0 22 * * fri",
                }
            },
            creator=self.user,
        )

    def test_update_chore_requires_permission(self):
        url = reverse("chore_update", kwargs={"pk": self.chore.id})
        success = self.client.login(
            email=self.user_no_permission.email, password="testpassword"
        )
        self.assertTrue(success)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_chore_get(self):
        url = reverse("chore_update", kwargs={"pk": self.chore.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode("utf-8")
        self.assertTemplateUsed(response, "chores/chore_crud.html")
        self.assertIn(self.chore.name, html)
        self.assertIn("0 22 * * fri", html)
        self.assertIn("233", html)

    def test_update_chore_post(self):
        url = reverse("chore_update", kwargs={"pk": self.chore.id})
        starting_from = "2025/05/10 14:56"
        response = self.client.post(
            url,
            {
                "name": "Test Chore",
                "description": "A test chore that needs volunteers.",
                "wiki_url": "https://example.com",
                "frequency": 23,
                "starting_from": starting_from,
                "cron": "0 22 * * mon",
                "duration_value": 1,
                "duration_unit": "w",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_chore = Chore.objects.get(name="Test Chore")
        self.assertEqual(
            updated_chore.description, "A test chore that needs volunteers."
        )
        self.assertEqual(updated_chore.wiki_url, "https://example.com")
        self.assertTemplateUsed(response, "chores/chore_detail.html")
        self.assertEqual(
            {
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "2025/05/10 14:56",
                    "crontab": "0 22 * * mon",
                    "take_one_every": 23,
                    "duration": "P7D",
                },
            },
            updated_chore.configuration,
        )


class GenerateEventsForChore(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="example@example.com",
        )
        permission = Permission.objects.get(
            codename="add_chore", content_type=ContentType.objects.get_for_model(Chore)
        )
        self.user.user_permissions.add(permission)

        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)

    @time_machine.travel("2025-05-10 14:56")
    def test_generate_events_for_chore_get(self):
        chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore that needs volunteers.",
            class_type="BasicChore",
            configuration={
                "events_generation": {
                    "event_type": "recurrent",
                    "take_one_every": 2,
                    "starting_time": "10/05/2024 14:56",
                    "crontab": "0 22 * * fri",
                    "duration": "PT7H",
                }
            },
            creator=self.user,
        )

        url = reverse("generate_events_for_chore", kwargs={"pk": chore.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, reverse("chore_detail", kwargs={"pk": chore.id}))

        response = self.client.get(url)

        events = Agenda.objects.all()
        self.assertEqual(len(events), 2)
