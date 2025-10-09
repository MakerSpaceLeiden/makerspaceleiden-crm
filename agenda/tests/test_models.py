from datetime import date, datetime, time, timedelta, timezone

import time_machine
from django.test import TestCase

from acl.models import User
from agenda.models import Agenda
from chores.models import Chore


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
        # Test that startdatetime is stored as UTC
        self.assertEqual(
            agenda.startdatetime, datetime(2025, 5, 3, 7, 0, tzinfo=timezone.utc)
        )

        # Test that startdatetime is stored as UTC
        self.assertEqual(
            agenda.enddatetime, datetime(2025, 5, 3, 8, 0, tzinfo=timezone.utc)
        )

    def teststartdatetime_field_is_none_if_missing(self):
        agenda = Agenda.objects.create(
            startdate=None,
            starttime=None,
            enddate=date(2025, 5, 3),
            endtime=time(10, 0),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertIsNone(agenda.startdatetime)

        agenda2 = Agenda.objects.create(
            startdate=date(2025, 5, 3),
            starttime=None,
            enddate=date(2025, 5, 3),
            endtime=time(10, 0),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        self.assertIsNone(agenda2.startdatetime)

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

    @time_machine.travel("2025-05-10 12:00")
    def test_upcoming_includes_items_withenddatetime_gte_today(self):
        from datetime import datetime

        from django.utils import timezone as dj_timezone

        def make_agenda(start, end, title):
            return Agenda.objects.create(
                startdatetime=datetime(*start, tzinfo=dj_timezone.utc),
                enddatetime=datetime(*end, tzinfo=dj_timezone.utc),
                item_title=title,
                item_details="Test",
                user=self.user,
            )

        make_agenda((2025, 5, 8, 7, 0), (2025, 5, 10, 8, 0), "Ends today")
        make_agenda((2025, 5, 12, 7, 0), (2025, 5, 12, 8, 0), "Future")
        make_agenda((2025, 5, 1, 7, 0), (2025, 5, 5, 8, 0), "Past")

        upcoming = list(Agenda.objects.upcoming(days=10, limit=None))
        titles = [a.item_title for a in upcoming]
        self.assertIn("Ends today", titles)
        self.assertIn("Future", titles)
        self.assertNotIn("Past", titles)

    def test_set_status_creates_status_change_record(self):
        from agenda.models import AgendaChoreStatusChange

        other_user = User.objects.create_user(
            first_name="Other",
            last_name="User",
            password="testpassword",
            email="otheruser@example.com",
        )
        agenda = Agenda.objects.create(
            startdate=date(2025, 5, 3),
            starttime=time(9, 0),
            enddate=date(2025, 5, 3),
            endtime=time(10, 0),
            item_title="Test Agenda",
            item_details="Test details.",
            user=self.user,
        )
        # Initially no status change records
        self.assertEqual(AgendaChoreStatusChange.objects.count(), 0)
        # Set status to completed
        agenda.set_status("completed", other_user)
        self.assertEqual(agenda.status, "completed")
        # There should be one status change record
        changes = AgendaChoreStatusChange.objects.filter(agenda=agenda)
        self.assertEqual(changes.count(), 1)
        change = changes.first()
        self.assertEqual(change.status, "completed")
        self.assertEqual(change.user, other_user)
        # Setting to the same status again should not create a new record
        agenda.set_status("completed", self.user)
        self.assertEqual(
            AgendaChoreStatusChange.objects.filter(agenda=agenda).count(), 1
        )
        # Setting to a new status should create another record
        agenda.set_status("in_progress", self.user)
        self.assertEqual(agenda.status, "in_progress")
        self.assertEqual(
            AgendaChoreStatusChange.objects.filter(agenda=agenda).count(), 2
        )

    @time_machine.travel("2025-05-03 10:00")
    def test_life_cycle_properties(self):
        """
        Table-driven test for Agenda.is_active property.
        Each case defines start, end, current time, and expected result.
        """
        test_cases = [
            {
                "label": "active between start and end",
                "start": datetime(2025, 5, 3, 6, 0, tzinfo=timezone.utc),
                "end": datetime(2025, 5, 3, 16, 0, tzinfo=timezone.utc),
                "expected": True,
                "status": "help wanted",
            },
            {
                "label": "inactive before start",
                "start": datetime(2025, 5, 2, 9, 0, tzinfo=timezone.utc),
                "end": datetime(2025, 5, 2, 10, 0, tzinfo=timezone.utc),
                "expected": False,
                "status": "pending",
            },
            {
                "label": "inactive after end",
                "start": datetime(2025, 5, 3, 9, 0, tzinfo=timezone.utc),
                "end": datetime(2025, 5, 3, 10, 0, tzinfo=timezone.utc),
                "expected": False,
                "status": "pending",
            },
        ]

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
        for case in test_cases:
            with self.subTest(msg=case["label"]):
                agenda = Agenda.objects.create(
                    startdatetime=case["start"],
                    enddatetime=case["end"],
                    item_title=case["label"],
                    user=self.user,
                    chore=chore,
                )
                self.assertEqual(agenda.is_active, case["expected"])
                self.assertEqual(agenda.display_status, case["status"])

    def test_display_datetime(self):
        test_cases = [
            {
                "label": "single day event",
                "start": datetime(2025, 5, 3, 8, 0, tzinfo=timezone.utc),
                "end": datetime(2025, 5, 3, 9, 0, tzinfo=timezone.utc),
                "expected": "Saturday, 3/5 10–11h",
            },
            {
                "label": "single day event",
                "start": datetime(2025, 5, 3, 6, 0, tzinfo=timezone.utc),
                "end": datetime(2025, 5, 10, 16, 0, tzinfo=timezone.utc),
                "expected": "Saturday, 3–10/5",
            },
        ]
        for case in test_cases:
            with self.subTest(msg=case["label"]):
                agenda = Agenda.objects.create(
                    startdatetime=case["start"],
                    enddatetime=case["end"],
                    item_title=case["label"],
                    user=self.user,
                )
                self.assertEqual(agenda.display_datetime, case["expected"])

    @time_machine.travel("2025-05-06 10:00")
    def test_create_occurrence(self):
        agenda = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 3, 8, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 3, 16, 0, tzinfo=timezone.utc),
            item_title="Test Agenda",
            recurrences="FREQ=WEEKLY;INTERVAL=1;BYDAY=SA",
            user=self.user,
        )

        start = datetime.now(tz=timezone.utc)
        end = start + timedelta(days=6)

        created_first = Agenda.objects.create_occurrence(
            parent=agenda,
            start_datetime=start,
            end_datetime=end,
        )

        created_second = Agenda.objects.create_occurrence(
            parent=agenda,
            start_datetime=start,
            end_datetime=end,
        )

        child_items = Agenda.objects.filter(recurrence_parent=agenda)

        # Get the duration of the first occurrence
        duration_created = created_first[0].enddatetime - created_first[0].startdatetime
        self.assertEqual(agenda.enddatetime - agenda.startdatetime, duration_created)

        self.assertEqual(child_items.count(), 1)
        self.assertEqual(len(created_first), 1)
        self.assertEqual(len(created_second), 0)
