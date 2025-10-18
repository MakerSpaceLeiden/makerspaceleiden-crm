from datetime import datetime, timezone

import time_machine
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from acl.models import User
from agenda.models import Agenda


class AgendaCreateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="example@example.com",
        )
        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)

    def test_agenda_create_get(self):
        url = reverse("agenda_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "agenda/agenda_crud.html")

    @time_machine.travel("2025-05-10 14:56")
    def test_agenda_view(self):
        url = reverse("agenda_detail", kwargs={"pk": 1})

        original = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 10, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 10, 15, 0, tzinfo=timezone.utc),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )

        response = self.client.get(url + "?copy_from=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode("utf-8")
        self.assertTemplateUsed(response, "agenda/agenda_detail.html")
        self.assertIn(original.item_title, html)
        self.assertIn(original.item_details, html)

    @time_machine.travel("2025-05-10 14:56")
    def test_agenda_create_copy_from(self):
        url = reverse("agenda_create")

        original = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 10, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 10, 10, 0, tzinfo=timezone.utc),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )

        response = self.client.get(url + "?copy_from=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode("utf-8")
        self.assertTemplateUsed(response, "agenda/agenda_crud.html")
        self.assertIn(original.item_title, html)
        self.assertIn(original.item_details, html)
        self.assertIn("2025-05-17", html, "Suggested dates")

    @time_machine.travel("2025-05-05 14:56")
    def test_agenda_create_copy_from_on_a_saturday(self):
        url = reverse("agenda_create")

        original = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 3, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 3, 10, 0, tzinfo=timezone.utc),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )

        response = self.client.get(url + "?copy_from=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode("utf-8")
        self.assertTemplateUsed(response, "agenda/agenda_crud.html")
        self.assertIn(original.item_title, html)
        self.assertIn(original.item_details, html)
        self.assertIn("2025-05-10", html, "Suggested dates")
        self.assertIn("11:00", html, "Suggested time")


class AgendaUpdateViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="example@example.com",
        )
        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)

    def test_agenda_update_get(self):
        self.assertTrue(
            self.client.login(email=self.user.email, password="testpassword")
        )

        chore = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 10, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 10, 10, 0, tzinfo=timezone.utc),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )

        url = reverse("agenda_update", kwargs={"pk": chore.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "agenda/agenda_crud.html")
        self.assertNotContains(
            response, 'data-test-hook="recurrence-parent-agenda-item-found"'
        )
        self.assertContains(response, 'data-test-hook="recurrence-rule-input"')

    def test_agenda_update_get_with_recurrence_parent(self):
        self.assertTrue(
            self.client.login(email=self.user.email, password="testpassword")
        )

        parent = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 10, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 10, 10, 0, tzinfo=timezone.utc),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )

        chore = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 10, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 10, 10, 0, tzinfo=timezone.utc),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
            recurrence_parent=parent,
        )

        url = reverse("agenda_update", kwargs={"pk": chore.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "agenda/agenda_crud.html")
        self.assertContains(
            response, 'data-test-hook="recurrence-parent-agenda-item-found"'
        )
        self.assertNotContains(response, 'data-test-hook="recurrence-rule-input"')


class AgendaItemsView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="example@example.com",
        )

    def test_requires_login(self):
        url = reverse("agenda")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_list_get(self):
        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)
        url = reverse("agenda")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, "agenda/agenda_list.html")


class AgendaUpdateStatusViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="An",
            last_name="Example",
            password="testpassword",
            email="example@example.com",
        )
        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)

    def test_agenda_update_status_get(self):
        self.assertTrue(
            self.client.login(email=self.user.email, password="testpassword")
        )

        chore = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 10, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 10, 10, 0, tzinfo=timezone.utc),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )

        url = reverse("agenda_update_status", kwargs={"pk": chore.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(
            response.url,
            "/",
        )

    def test_agenda_update_status_post(self):
        self.assertTrue(
            self.client.login(email=self.user.email, password="testpassword")
        )

        chore = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 10, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 10, 10, 0, tzinfo=timezone.utc),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )

        url = reverse("agenda_update_status", kwargs={"pk": chore.id})
        response = self.client.post(url, {"status": "completed"})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "/")
        updated_chore = Agenda.objects.get(pk=chore.id)
        self.assertEqual(updated_chore.status, "completed")
