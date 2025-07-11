# Create your tests here.
from io import StringIO

import time_machine
from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from members.models import User

from .models import Chore


class CustomCommandTest(TestCase):
    @time_machine.travel("2025-07-10 19:56")
    def test_email_asking_for_volunteers(self):
        # Arrange
        # Create a test user
        user = User.objects.create_user(
            email="chore.author@example.com",
            password="testpass123",
            first_name="Task",
            last_name="User",
            telegram_user_id="987654321",
        )

        # Create a chore that requires a volunteer
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
            creator=user,
        )

        # Act
        out = StringIO()
        call_command("send_reminders", stdout=out)

        # Run twice to ensure duplicate notifications are not created
        call_command("send_reminders", stdout=out)

        # Assert that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(nudge_destination, email.to)
        self.assertIn("Volunteers needed next week", email.subject)
        self.assertIn("Hallo, we hebben 1 vrijwilliger", email.body)
