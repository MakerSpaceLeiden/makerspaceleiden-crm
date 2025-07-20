from datetime import date, datetime, time, timezone

import time_machine
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from acl.models import User
from agenda.models import Agenda
from chores.models import Chore


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

    def test_agenda_view(self):
        url = reverse("agenda_detail", kwargs={"pk": 1})

        original = Agenda.objects.create(
            startdate=date.today(),
            starttime=time(9, 0),
            enddate=date.today(),
            endtime=time(10, 0),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )

        response = self.client.get(url + "?copy_from=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        html = response.content.decode("utf-8")
        self.assertTemplateUsed(response, "agenda/agenda.html")
        self.assertIn(original.item_title, html)
        self.assertIn(original.item_details, html)

    @time_machine.travel("2025-05-10 14:56")
    def test_agenda_create_copy_from(self):
        url = reverse("agenda_create")

        original = Agenda.objects.create(
            startdate=date.today(),
            starttime=time(9, 0),
            enddate=date.today(),
            endtime=time(10, 0),
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
            startdate=datetime.strptime("2025-05-03", "%Y-%m-%d").date(),
            starttime=time(9, 0),
            enddate=datetime.strptime("2025-05-03", "%Y-%m-%d").date(),
            endtime=time(10, 0),
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


class AgendaModelPropertiesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="Model",
            last_name="Test",
            password="testpassword",
            email="modeltest@example.com",
        )

    def test_start_datetime_and_end_datetime_present(self):
        agenda = Agenda.objects.create(
            startdate=date(2025, 5, 3),
            starttime=time(9, 0),
            enddate=date(2025, 5, 3),
            endtime=time(10, 0),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertEqual(
            agenda.start_datetime, datetime(2025, 5, 3, 7, 0, tzinfo=timezone.utc)
        )
        self.assertEqual(
            agenda.end_datetime, datetime(2025, 5, 3, 8, 0, tzinfo=timezone.utc)
        )
        # Test that _startdatetime is stored as UTC
        self.assertEqual(
            agenda._startdatetime, datetime(2025, 5, 3, 7, 0, tzinfo=timezone.utc)
        )

        # Test that _startdatetime is stored as UTC
        self.assertEqual(
            agenda._enddatetime, datetime(2025, 5, 3, 8, 0, tzinfo=timezone.utc)
        )

    def test_startdatetime_field_is_none_if_missing(self):
        agenda = Agenda.objects.create(
            startdate=None,
            starttime=None,
            enddate=date(2025, 5, 3),
            endtime=time(10, 0),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertIsNone(agenda._startdatetime)

        agenda2 = Agenda.objects.create(
            startdate=date(2025, 5, 3),
            starttime=None,
            enddate=date(2025, 5, 3),
            endtime=time(10, 0),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertIsNone(agenda2._startdatetime)

    def test_start_datetime_missing_time(self):
        agenda = Agenda.objects.create(
            startdate=date(2025, 5, 3),
            starttime=None,
            enddate=date(2025, 5, 3),
            endtime=time(10, 0),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertIsNone(agenda.start_datetime)
        self.assertEqual(
            agenda.end_datetime, datetime(2025, 5, 3, 8, 0, tzinfo=timezone.utc)
        )

    def test_end_datetime_missing_date(self):
        agenda = Agenda.objects.create(
            startdate=date(2025, 5, 3),
            starttime=time(9, 0),
            enddate=None,
            endtime=time(10, 0),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertEqual(
            agenda.start_datetime, datetime(2025, 5, 3, 7, 0, tzinfo=timezone.utc)
        )
        self.assertIsNone(agenda.end_datetime)

    def test_both_missing(self):
        agenda = Agenda.objects.create(
            startdate=None,
            starttime=None,
            enddate=None,
            endtime=None,
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertIsNone(agenda.start_datetime)
        self.assertIsNone(agenda.end_datetime)

    def test_type(self):
        chore = Chore.objects.create(
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
        agendaTypeChore = Agenda.objects.create(
            startdate=None,
            starttime=None,
            enddate=None,
            endtime=None,
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
            chore=chore,
        )
        self.assertEqual("chore", agendaTypeChore.type)

        agendaTypeSocial = Agenda.objects.create(
            startdate=None,
            starttime=None,
            enddate=None,
            endtime=None,
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertEqual("social", agendaTypeSocial.type)
