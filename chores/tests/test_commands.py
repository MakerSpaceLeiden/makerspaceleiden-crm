from datetime import datetime, timezone
from io import StringIO

import time_machine
from django.core.management import call_command
from django.test import TestCase

from agenda.models import Agenda

from ..models import Chore
from .factories import UserFactory


class CustomCommandTest(TestCase):
    def setUp(self):
        self.user = UserFactory(
            email="chore.author@example.com",
        )

    @time_machine.travel("2025-07-15 14:56")
    def test_generate_events(self):
        out = StringIO()
        Chore.objects.create(
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

        call_command("generate_events", limit=21, stdout=out)
        call_command("generate_events", limit=21, stdout=out)
        call_command("generate_events", limit=21, stdout=out)

        self.assertIn("Generating events for chores", out.getvalue())
        self.assertEqual(Agenda.objects.count(), 3)
        agenda = Agenda.objects.first()
        self.assertEqual(agenda.item_title, "Test Chore")
        self.assertEqual(agenda.item_details, "A test chore that needs volunteers.")
        self.assertEqual(
            agenda.start_datetime,
            datetime(2025, 7, 20, 20, 00, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(agenda.user, self.user)

    # Limit window of time to generate events for
    @time_machine.travel("2025-07-15 14:56")
    def test_generate_events_on_less_than_weekly_frequency(self):
        out = StringIO()
        Chore.objects.create(
            name="Test Chore",
            description="A test chore that needs volunteers.",
            class_type="BasicChore",
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

        call_command("generate_events", limit=21, stdout=out)
        call_command("generate_events", limit=21, stdout=out)

        self.assertIn("Generating events for chores", out.getvalue())
        self.assertEqual(Agenda.objects.count(), 2)
        agenda = Agenda.objects.first()
        self.assertEqual(agenda.item_title, "Test Chore")
        self.assertEqual(agenda.item_details, "A test chore that needs volunteers.")
        self.assertEqual(
            agenda.start_datetime,
            datetime(2025, 7, 20, 20, 00, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(agenda.user, self.user)

    # First occurence should be based on start date of chore not invocation
    # of the command
    @time_machine.travel("2025-07-19 14:56")
    def test_generate_events_informed_by_starting_date(self):
        out = StringIO()
        Chore.objects.create(
            name="test_chore",
            description="A test chore that runs every 12 weeks",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "8/3/2020 7:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 11,
                },
                "reminders": [],
            },
            creator=self.user,
        )

        call_command("generate_events", limit=90, stdout=out)
        call_command("generate_events", limit=90, stdout=out)

        self.assertIn("Generating events for chores", out.getvalue())
        self.assertEqual(Agenda.objects.count(), 1)
        agenda = Agenda.objects.first()
        self.assertEqual(agenda.item_title, "Test Chore")
        self.assertEqual(agenda.item_details, "A test chore that runs every 12 weeks")
        self.assertEqual(
            agenda.start_datetime,
            datetime(2025, 8, 31, 20, 00, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(agenda.user, self.user)
