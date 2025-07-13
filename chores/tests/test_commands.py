# Create your tests here.
import random
from io import StringIO

import time_machine
from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from ..models import Chore, ChoreNotification, ChoreVolunteer
from .factories import UserFactory


class CustomCommandTest(TestCase):
    def setUp(self):
        self.user = UserFactory(
            email="chore.author@example.com",
        )

    @time_machine.travel("2025-07-10 19:56")
    def test_email_asking_for_volunteers(self):
        # Arrange

        # Create a chore that requires a volunteer
        # Switch to faker for generating these email addresses
        nudge_destination = "deelnemers@makerspaceleiden.nl"
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
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "gentle_email_reminder",
                                "destination": nudge_destination,
                                "subject_template": "Volunteers needed next week",
                                "body_template": "Hallo, we hebben {num_volunteers_needed} vrijwilliger nodig volgende week.\n\nOm stof in onze makerspace tegen te gaan willen we je vragen om te stofzuigen in de voorste ruimte en de houtwerkplaats, en eventueel de grote hal. \n\nAls je daar zin in hebt kun je ook de voorste ruimte dweilen met de hippe turbodweil die we hebben, maar als je weinig tijd hebt: Met alleen stofzuigen is al veel te winnen.\n\nDeze taak kan op elk moment gedurende de week worden gedaan. Je helpt wanneer het jou uitkomt, alle hulp is welkom!\n\nInformatie over schoonmaken op de Wiki: https://wiki.makerspaceleiden.nl/mediawiki/index.php/Chore_-_Dedustify \n\n\nClick here to sign up: {signup_url}",
                            }
                        ],
                    },
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 6, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "hard_email_reminder",
                                "destination": nudge_destination,
                                "subject_template": "Volunteers REALLY needed for this week",
                                "body_template": "Hallo, we hebben nog steeds {num_volunteers_needed} vrijwilliger nodig voor deze week.\n\nOm stof in onze makerspace tegen te gaan willen we je vragen om te stofzuigen in de voorste ruimte en de houtwerkplaats, en eventueel de grote hal. \n\nAls je daar zin in hebt kun je ook de voorste ruimte dweilen met de hippe turbodweil die we hebben, maar als je weinig tijd hebt: Met alleen stofzuigen is al veel te winnen.\n\nDeze taak kan op elk moment gedurende de week worden gedaan. Je helpt wanneer het jou uitkomt, alle hulp is welkom!\n\nInformatie over schoonmaken op de Wiki: https://wiki.makerspaceleiden.nl/mediawiki/index.php/Chore_-_Dedustify \n\nClick here to sign up: {signup_url}",
                            }
                        ],
                    },
                    {
                        "reminder_type": "volunteers_who_signed_up",
                        "when": {"days_before": 7, "time": "19:00"},
                    },
                ],
            },
            creator=self.user,
        )

        out = StringIO()

        # Act – run at least once to ensure duplicate notifications are not created
        n = random.randint(2, 4)
        for _ in range(n):
            call_command("send_reminders", stdout=out)

        # Assert that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(ChoreNotification.objects.count(), 1)
        chore_notification = ChoreNotification.objects.first()
        self.assertEqual(nudge_destination, chore_notification.recipient_other)
        email = mail.outbox[0]
        self.assertIn(nudge_destination, email.to)
        self.assertIn("Volunteers needed next week", email.subject)
        self.assertIn("Hallo, we hebben 1 vrijwilliger", email.body)

    @time_machine.travel("2025-07-14 19:56")
    def test_urgent_email_asking_for_volunteers(self):
        # Arrange
        # Create a chore that requires a volunteer
        # Switch to faker for generating these email addresses
        nudge_destination = "deelnemers@makerspaceleiden.nl"
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
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "gentle_email_reminder",
                                "destination": nudge_destination,
                                "subject_template": "Volunteers needed next week",
                                "body_template": "Hallo, we hebben {num_volunteers_needed} vrijwilliger nodig volgende week.\n\nOm stof in onze makerspace tegen te gaan willen we je vragen om te stofzuigen in de voorste ruimte en de houtwerkplaats, en eventueel de grote hal. \n\nAls je daar zin in hebt kun je ook de voorste ruimte dweilen met de hippe turbodweil die we hebben, maar als je weinig tijd hebt: Met alleen stofzuigen is al veel te winnen.\n\nDeze taak kan op elk moment gedurende de week worden gedaan. Je helpt wanneer het jou uitkomt, alle hulp is welkom!\n\nInformatie over schoonmaken op de Wiki: https://wiki.makerspaceleiden.nl/mediawiki/index.php/Chore_-_Dedustify \n\n\nClick here to sign up: {signup_url}",
                            }
                        ],
                    },
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 6, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "hard_email_reminder",
                                "destination": nudge_destination,
                                "subject_template": "Volunteers REALLY needed for this week",
                                "body_template": "Hallo, we hebben nog steeds {num_volunteers_needed} vrijwilliger nodig voor deze week.\n\nOm stof in onze makerspace tegen te gaan willen we je vragen om te stofzuigen in de voorste ruimte en de houtwerkplaats, en eventueel de grote hal. \n\nAls je daar zin in hebt kun je ook de voorste ruimte dweilen met de hippe turbodweil die we hebben, maar als je weinig tijd hebt: Met alleen stofzuigen is al veel te winnen.\n\nDeze taak kan op elk moment gedurende de week worden gedaan. Je helpt wanneer het jou uitkomt, alle hulp is welkom!\n\nInformatie over schoonmaken op de Wiki: https://wiki.makerspaceleiden.nl/mediawiki/index.php/Chore_-_Dedustify \n\nClick here to sign up: {signup_url}",
                            }
                        ],
                    },
                    {
                        "reminder_type": "volunteers_who_signed_up",
                        "when": {"days_before": 7, "time": "19:00"},
                    },
                ],
            },
            creator=self.user,
        )
        out = StringIO()

        # Act – run at least once to ensure duplicate notifications are not created
        n = random.randint(2, 4)
        for _ in range(n):
            call_command("send_reminders", stdout=out)

        # Assert that emails were sent
        self.assertEqual(len(mail.outbox), 2)
        self.assertGreaterEqual(ChoreNotification.objects.count(), 1)
        chore_notification = ChoreNotification.objects.last()
        self.assertEqual(nudge_destination, chore_notification.recipient_other)
        email = mail.outbox[1]
        self.assertIn(nudge_destination, email.to)
        self.assertIn("Volunteers REALLY needed for this week", email.subject)
        self.assertIn("Hallo, we hebben nog steeds 1 vrijwilliger", email.body)

    @time_machine.travel("2025-07-13 21:56")
    def test_email_reminding_volunteers(self):
        # Arrange
        # Create a chore that requires a volunteer
        # Switch to faker for generating these email addresses
        nudge_destination = "deelnemers@makerspaceleiden.nl"
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
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "gentle_email_reminder",
                                "destination": nudge_destination,
                                "subject_template": "Volunteers needed next week",
                                "body_template": "Hallo, we hebben {num_volunteers_needed} vrijwilliger nodig volgende week.\n\nOm stof in onze makerspace tegen te gaan willen we je vragen om te stofzuigen in de voorste ruimte en de houtwerkplaats, en eventueel de grote hal. \n\nAls je daar zin in hebt kun je ook de voorste ruimte dweilen met de hippe turbodweil die we hebben, maar als je weinig tijd hebt: Met alleen stofzuigen is al veel te winnen.\n\nDeze taak kan op elk moment gedurende de week worden gedaan. Je helpt wanneer het jou uitkomt, alle hulp is welkom!\n\nInformatie over schoonmaken op de Wiki: https://wiki.makerspaceleiden.nl/mediawiki/index.php/Chore_-_Dedustify \n\n\nClick here to sign up: {signup_url}",
                            }
                        ],
                    },
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 6, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "hard_email_reminder",
                                "destination": nudge_destination,
                                "subject_template": "Volunteers REALLY needed for this week",
                                "body_template": "Hallo, we hebben nog steeds {num_volunteers_needed} vrijwilliger nodig voor deze week.\n\nOm stof in onze makerspace tegen te gaan willen we je vragen om te stofzuigen in de voorste ruimte en de houtwerkplaats, en eventueel de grote hal. \n\nAls je daar zin in hebt kun je ook de voorste ruimte dweilen met de hippe turbodweil die we hebben, maar als je weinig tijd hebt: Met alleen stofzuigen is al veel te winnen.\n\nDeze taak kan op elk moment gedurende de week worden gedaan. Je helpt wanneer het jou uitkomt, alle hulp is welkom!\n\nInformatie over schoonmaken op de Wiki: https://wiki.makerspaceleiden.nl/mediawiki/index.php/Chore_-_Dedustify \n\nClick here to sign up: {signup_url}",
                            }
                        ],
                    },
                    {
                        "reminder_type": "volunteers_who_signed_up",
                        "when": {"days_before": 7, "time": "19:00"},
                    },
                ],
            },
            creator=self.user,
        )
        volunteeruser = UserFactory(
            email="chore.volunteer@example.com",
        )
        ChoreVolunteer.objects.create(
            user=volunteeruser, chore=chore, timestamp=1753041600
        )

        out = StringIO()

        # Act – run at least once to ensure duplicate notifications are not created
        n = random.randint(2, 3)
        for _ in range(n):
            call_command("send_reminders", stdout=out)

        # Assert that emails were sent
        self.assertEqual(ChoreNotification.objects.all().count(), 1)
        chore_notification = ChoreNotification.objects.last()
        self.assertIsNone(chore_notification.recipient_other)
        self.assertEqual(volunteeruser, chore_notification.recipient_user)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(volunteeruser.email, email.to)
        self.assertIn("Volunteering reminder", email.subject)
        self.assertIn("friendly reminder that you signed up for", email.body)


class SingleOccurrenceChoreTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @time_machine.travel("2025-07-10 19:56")
    def test_single_occurrence_chore_reminder(self):
        """Test reminder for single occurrence chore"""
        nudge_destination = "deelnemers@makerspaceleiden.nl"
        Chore.objects.create(
            name="Single Event Chore",
            description="A one-time chore",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "single_occurrence",
                    "event_time": "21/7/2025 8:00",
                },
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "single_occurrence_reminder",
                                "destination": nudge_destination,
                                "subject_template": "Single event reminder",
                                "body_template": "Reminder for single event: {event_day}",
                            }
                        ],
                    },
                ],
            },
            creator=self.user,
        )

        out = StringIO()
        call_command("send_reminders", stdout=out)

        # Should not send reminder since event is in the future
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(ChoreNotification.objects.count(), 0)


class NoVolunteersNeededTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @time_machine.travel("2025-07-10 19:56")
    def test_no_reminder_when_volunteers_exist(self):
        """Test that no reminder is sent when volunteers are already signed up"""
        nudge_destination = "deelnemers@makerspaceleiden.nl"
        chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "gentle_email_reminder",
                                "destination": nudge_destination,
                                "subject_template": "Test reminder",
                                "body_template": "Test body",
                            }
                        ],
                    },
                ],
            },
            creator=self.user,
        )

        # Create a volunteer
        volunteer_user = UserFactory()
        ChoreVolunteer.objects.create(
            user=volunteer_user,
            chore=chore,
            timestamp=1753041600,
        )

        out = StringIO()
        call_command("send_reminders", stdout=out)

        # Should not send reminder since volunteer is already signed up
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(ChoreNotification.objects.count(), 0)


class InvalidChoreTypeTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_invalid_chore_type_raises_exception(self):
        """Test that invalid chore type raises exception"""
        Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="InvalidChoreType",
            configuration={"min_required_people": 1},
            creator=self.user,
        )

        out = StringIO()
        with self.assertRaises(
            Exception
        ):  # Should raise exception for invalid chore type
            call_command("send_reminders", stdout=out)


class InvalidReminderTypeTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_invalid_reminder_type_raises_exception(self):
        """Test that invalid reminder type raises exception"""
        Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "invalid_reminder_type",
                        "when": {"days_before": 10, "time": "17:00"},
                    },
                ],
            },
            creator=self.user,
        )

        out = StringIO()
        with self.assertRaises(
            Exception
        ):  # Should raise exception for invalid reminder type
            call_command("send_reminders", stdout=out)


class MultipleVolunteersTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @time_machine.travel("2025-07-13 21:56")
    def test_multiple_volunteers_reminder(self):
        """Test reminder for multiple volunteers"""
        chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={
                "min_required_people": 2,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "volunteers_who_signed_up",
                        "when": {"days_before": 7, "time": "19:00"},
                    },
                ],
            },
            creator=self.user,
        )

        # Create multiple volunteers
        volunteer1 = UserFactory(
            email="volunteer1@example.com",
        )
        volunteer2 = UserFactory(
            email="volunteer2@example.com",
        )

        ChoreVolunteer.objects.create(
            user=volunteer1,
            chore=chore,
            timestamp=1753041600,
        )
        ChoreVolunteer.objects.create(
            user=volunteer2,
            chore=chore,
            timestamp=1753041600,
        )

        out = StringIO()
        call_command("send_reminders", stdout=out)

        # Should send reminders to both volunteers
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(ChoreNotification.objects.count(), 2)

        # Check that both volunteers received notifications
        notification_emails = [email.to[0] for email in mail.outbox]
        self.assertIn(volunteer1.email, notification_emails)
        self.assertIn(volunteer2.email, notification_emails)


class MultipleChoresTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @time_machine.travel("2025-07-10 19:56")
    def test_multiple_chores_processed(self):
        """Test that multiple chores are processed correctly"""
        # Create multiple chores
        chore1 = Chore.objects.create(
            name="Chore 1",
            description="First test chore",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "chore1_reminder",
                                "destination": "deelnemers@makerspaceleiden.nl",
                                "subject_template": "Chore 1 reminder",
                                "body_template": "Reminder for chore 1",
                            }
                        ],
                    },
                ],
            },
            creator=self.user,
        )

        chore2 = Chore.objects.create(
            name="Chore 2",
            description="Second test chore",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "chore2_reminder",
                                "destination": "deelnemers@makerspaceleiden.nl",
                                "subject_template": "Chore 2 reminder",
                                "body_template": "Reminder for chore 2",
                            }
                        ],
                    },
                ],
            },
            creator=self.user,
        )

        out = StringIO()
        call_command("send_reminders", stdout=out)

        # Should send reminders for both chores
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(ChoreNotification.objects.count(), 2)

        # Check that both chores generated notifications
        notification_chores = [
            notification.chore for notification in ChoreNotification.objects.all()
        ]
        self.assertIn(chore1, notification_chores)
        self.assertIn(chore2, notification_chores)


class NoChoresTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @time_machine.travel("2025-07-10 19:56")
    def test_no_chores_no_emails(self):
        """Test that no emails are sent when no chores exist"""
        out = StringIO()
        call_command("send_reminders", stdout=out)

        # Should not send any emails when no chores exist
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(ChoreNotification.objects.count(), 0)


class FutureEventTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @time_machine.travel("2025-07-10 19:56")
    def test_future_event_no_reminder(self):
        """Test that no reminder is sent for future events"""
        Chore.objects.create(
            name="Future Chore",
            description="A chore with future events",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2025 8:00",  # Future date
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "future_reminder",
                                "destination": "deelnemers@makerspaceleiden.nl",
                                "subject_template": "Future reminder",
                                "body_template": "Future reminder body",
                            }
                        ],
                    },
                ],
            },
            creator=self.user,
        )

        out = StringIO()
        call_command("send_reminders", stdout=out)

        # Should not send reminder for future events
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(ChoreNotification.objects.count(), 0)


class VolunteerCrossContaminationTest(TestCase):
    """Test the defect where volunteers from one chore incorrectly affect another chore's reminder logic"""

    def setUp(self):
        self.user = UserFactory()

    @time_machine.travel("2025-07-10 19:56")
    def test_volunteer_cross_contamination_defect(self):
        """Test that volunteers from one chore do not prevent reminders for another chore"""
        # Create first chore that needs volunteers
        chore1 = Chore.objects.create(
            name="Chore 1 - Needs Volunteers",
            description="A chore that needs volunteers",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "chore1_reminder",
                                "destination": "deelnemers@makerspaceleiden.nl",
                                "subject_template": "Chore 1 needs volunteers",
                                "body_template": "Chore 1 needs volunteers",
                            }
                        ],
                    },
                ],
            },
            creator=self.user,
        )

        # Create second chore that also needs volunteers
        Chore.objects.create(
            name="Chore 2 - Needs Volunteers",
            description="Another chore that needs volunteers",
            class_type="BasicChore",
            configuration={
                "min_required_people": 1,
                "events_generation": {
                    "event_type": "recurrent",
                    "starting_time": "21/7/2021 8:00",
                    "crontab": "0 22 * * sun",
                    "take_one_every": 2,
                },
                "reminders": [
                    {
                        "reminder_type": "missing_volunteers",
                        "when": {"days_before": 10, "time": "17:00"},
                        "nudges": [
                            {
                                "nudge_type": "email",
                                "nudge_key": "chore2_reminder",
                                "destination": "deelnemers@makerspaceleiden.nl",
                                "subject_template": "Chore 2 needs volunteers",
                                "body_template": "Chore 2 needs volunteers",
                            }
                        ],
                    },
                ],
            },
            creator=self.user,
        )

        # Create a volunteer for chore1 only
        volunteer = UserFactory()
        ChoreVolunteer.objects.create(
            user=volunteer,
            chore=chore1,  # Only volunteer for chore1
            timestamp=1753041600,
        )

        out = StringIO()
        call_command("send_reminders", stdout=out)

        # Verify that chore2 should have gotten a reminder if the bug was fixed
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Chore 2 needs volunteers", mail.outbox[0].subject)
