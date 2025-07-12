# Create your tests here.
import random
from io import StringIO

import time_machine
from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from members.models import User

from .models import Chore, ChoreNotification, ChoreVolunteer


class CustomCommandTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="chore.author@example.com",
            password="testpass123",
            first_name="Task",
            last_name="User",
            telegram_user_id="987654321",
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
        volunteeruser = User.objects.create_user(
            email="chore.volunteer@example.com",
            password="testpass123",
            first_name="Task",
            last_name="Volunteer",
            telegram_user_id="987654322",
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
