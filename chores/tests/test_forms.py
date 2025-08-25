from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..forms import ChoreForm
from ..models import Chore

User = get_user_model()


class ChoreFormTest(TestCase):
    """Test the ChoreForm save functionality"""

    def setUp(self):
        self.form_data = {
            "name": "Test Chore",
            "description": "Test chore description",
            "wiki_url": "https://wiki.example.com/test",
            "frequency": 2,
            "starting_from": "2024/01/01 10:00",
            "cron": "0 10 * * 1",
            "duration_value": 5,
            "duration_unit": "d",
        }

    def test_save_creates_correct_duration_string_days(self):
        """Test that save creates correct duration string for days"""
        form = ChoreForm(data=self.form_data)
        self.assertTrue(form.is_valid())

        instance = form.save()

        expected_duration = "P5D"
        actual_duration = instance.configuration["events_generation"]["duration"]
        self.assertEqual(actual_duration, expected_duration)

    def test_save_creates_correct_duration_string_weeks(self):
        """Test that save creates correct duration string for weeks"""
        form_data = self.form_data.copy()
        form_data["duration_value"] = 3
        form_data["duration_unit"] = "w"

        form = ChoreForm(data=form_data)
        self.assertTrue(form.is_valid())

        instance = form.save()

        expected_duration = "P21D"
        actual_duration = instance.configuration["events_generation"]["duration"]
        self.assertEqual(actual_duration, expected_duration)

    def test_save_creates_correct_duration_string_hours(self):
        """Test that save creates correct duration string for hours"""
        form_data = self.form_data.copy()
        form_data["duration_value"] = 48
        form_data["duration_unit"] = "h"

        form = ChoreForm(data=form_data)
        self.assertTrue(form.is_valid())

        instance = form.save()

        expected_duration = "P2D"
        actual_duration = instance.configuration["events_generation"]["duration"]
        self.assertEqual(actual_duration, expected_duration)

    def test_save_preserves_all_configuration_fields(self):
        """Test that save preserves all events_generation configuration fields"""
        form = ChoreForm(data=self.form_data)
        self.assertTrue(form.is_valid())

        instance = form.save()
        config = instance.configuration["events_generation"]

        self.assertEqual(config["take_one_every"], 2)
        self.assertEqual(config["event_type"], "recurrent")
        self.assertEqual(config["starting_time"], "2024/01/01 10:00")
        self.assertEqual(config["crontab"], "0 10 * * 1")
        self.assertEqual(config["duration"], "P5D")

    def test_save_with_existing_instance_updates_configuration(self):
        """Test that save updates configuration on existing instance"""
        # Create existing chore
        chore = Chore.objects.create(
            name="Existing Chore",
            description="Existing description",
            wiki_url="https://wiki.example.com/existing",
            configuration={"events_generation": {"duration": "P1W"}},
        )

        # Update with form
        form_data = self.form_data.copy()
        form_data["duration_value"] = 10
        form_data["duration_unit"] = "d"

        form = ChoreForm(data=form_data, instance=chore)
        self.assertTrue(form.is_valid())

        updated_instance = form.save()

        expected_duration = "P10D"
        actual_duration = updated_instance.configuration["events_generation"][
            "duration"
        ]
        self.assertEqual(actual_duration, expected_duration)

    def test_form_initialization_parses_existing_duration(self):
        """Test that form initialization correctly parses existing duration"""
        chore = Chore.objects.create(
            name="Existing Chore",
            description="Existing description",
            wiki_url="https://wiki.example.com/existing",
            configuration={
                "events_generation": {
                    "duration": "P14W",
                    "take_one_every": 1,
                    "crontab": "0 9 * * 1",
                    "starting_time": datetime.now(),
                }
            },
        )

        form = ChoreForm(instance=chore)

        self.assertEqual(form.fields["duration_value"].initial, 98)
        self.assertEqual(form.fields["duration_unit"].initial, "D")

    def test_form_initialization_parses_existing_duration_hours(self):
        """Test that form initialization correctly parses existing duration"""
        chore = Chore.objects.create(
            name="Existing Chore",
            description="Existing description",
            wiki_url="https://wiki.example.com/existing",
            configuration={
                "events_generation": {
                    "duration": "PT21H",
                    "take_one_every": 1,
                    "crontab": "0 9 * * 1",
                    "starting_time": datetime.now(),
                }
            },
        )

        form = ChoreForm(instance=chore)

        self.assertEqual(form.fields["duration_value"].initial, 21)
        self.assertEqual(form.fields["duration_unit"].initial, "H")

    def test_form_initialization_parses_existing_duration_days(self):
        """Test that form initialization correctly parses existing duration"""
        chore = Chore.objects.create(
            name="Existing Chore",
            description="Existing description",
            wiki_url="https://wiki.example.com/existing",
            configuration={
                "events_generation": {
                    "duration": "P7D",
                    "take_one_every": 1,
                    "crontab": "0 9 * * 1",
                    "starting_time": datetime.now(),
                }
            },
        )

        form = ChoreForm(instance=chore)

        self.assertEqual(form.fields["duration_value"].initial, 7)
        self.assertEqual(form.fields["duration_unit"].initial, "D")
