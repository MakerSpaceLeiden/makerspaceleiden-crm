import json

import time_machine
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from faker import Faker
from rest_framework import status

from ..models import Chore, ChoreVolunteer
from .factories import UserFactory

fake = Faker()

User = get_user_model()


# Load the schema from a file
def load_schema(schema_path):
    with open(schema_path, "r") as schema_file:
        return json.load(schema_file)


class ChoresViewsTest(TestCase):
    def setUp(self):
        self.user = UserFactory(
            password="testpassword"
        )

    def test_empty_chores_overview_200(self):
        """Test that the empty chores overview returns a 200 response"""
        url = reverse("chores")
        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data-test-hook="empty-chores"', response.content.decode("utf-8"))

    def test_chores_overview_with_chore_200(self):
        url = reverse("chores")
        chore = Chore.objects.create(
            name=fake.name(),
            description="A test chore that needs volunteers.",
            class_type="BasicChore",
            wiki_url=fake.url(),
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
                                "destination": "test@example.com",
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
                                "destination": "test@example.com",
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
        
        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)
        response = self.client.get(url)
        html = response.content.decode("utf-8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(chore.description, html)
        self.assertIn('data-test-hook="chores-volunteer-button"', html)
        self.assertNotIn('data-test-hook="chores-volunteer"', html)
        self.assertNotIn('data-test-hook="empty-chores"', html)


    def test_chores_overview_with_chore_and_volunteer_200(self):
        url = reverse("chores")
        chore = Chore.objects.create(
            name=fake.name(),
            description="A test chore that needs volunteers.",
            class_type="BasicChore",
            wiki_url=fake.url(),
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
                                "destination": "test@example.com",
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
                                "destination": "test@example.com",
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
        volunteer = UserFactory()
        ChoreVolunteer.objects.create(
            user=volunteer, chore=chore, timestamp=1753041600
        )

        success = self.client.login(email=self.user.email, password="testpassword")
        self.assertTrue(success)
        response = self.client.get(url)
        html = response.content.decode("utf-8")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(chore.description, html)
        self.assertIn('data-test-hook="chores-volunteer"', html)
        self.assertIn(volunteer.first_name, html)
        self.assertNotIn('data-test-hook="empty-chores"', html)


