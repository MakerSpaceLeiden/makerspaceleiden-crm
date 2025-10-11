from datetime import datetime, timezone
from io import StringIO

import time_machine
from django.core.management import call_command
from django.test import TestCase

from agenda.models import Agenda
from chores.tests.factories import UserFactory


class AgendaGenerateRecurringEvents(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @time_machine.travel("2025-05-06 10:00")
    def test_agenda_generate_recurring_events(self):
        # Add an Agenda item with a rrule defined
        Agenda.objects.create(
            user=self.user,
            item_title="Test Agenda",
            item_details="Test Description",
            startdatetime=datetime(2025, 5, 3, 8, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 3, 16, 0, tzinfo=timezone.utc),
            recurrences="FREQ=DAILY;INTERVAL=1",
        )

        stdout = StringIO()
        call_command("agenda_generate_recurring_events", stdout=stdout)
        call_command("agenda_generate_recurring_events", stdout=StringIO())

        items = Agenda.objects.all()
        print(stdout.getvalue())
        self.assertIn("Generated 31 recurring events", stdout.getvalue())
        self.assertEqual(len(items), 32)
