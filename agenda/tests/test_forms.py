from datetime import datetime, timezone
from unittest.mock import patch

from django.test import TestCase

from acl.models import User
from agenda.forms import AgendaForm, AgendaStatusForm
from agenda.models import Agenda, AgendaChoreStatusChange
from chores.models import Chore


class AgendaFormTest(TestCase):
    """Test the AgendaForm functionality focusing on business logic"""

    def setUp(self):
        self.user = User.objects.create_user(
            first_name="Test",
            last_name="User",
            password="testpassword",
            email="testuser@example.com",
        )

        self.valid_form_data = {
            "startdatetime": datetime(2025, 5, 15, 14, 0, tzinfo=timezone.utc),
            "enddatetime": datetime(2025, 5, 15, 16, 0, tzinfo=timezone.utc),
            "item_title": "Test Agenda Item",
            "item_details": "This is a test agenda item description.",
        }

    def test_form_with_valid_data(self):
        """Test that valid form data passes validation"""
        form = AgendaForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_form_requires_essential_fields(self):
        """Test that essential fields are required"""
        required_fields = ["startdatetime", "enddatetime", "item_title"]

        for field in required_fields:
            data = self.valid_form_data.copy()
            del data[field]
            form = AgendaForm(data=data)
            self.assertFalse(form.is_valid())
            self.assertIn(field, form.errors)

    def test_form_allows_optional_fields_empty(self):
        """Test that optional fields can be omitted"""
        data = self.valid_form_data.copy()
        del data["item_details"]

        form = AgendaForm(data=data)
        self.assertTrue(form.is_valid())

    def test_validation_of_rrule(self):
        data = self.valid_form_data.copy()
        data["recurrences"] = "RRULE:FREQ=DAILY;COUNT=5"

        form = AgendaForm(data=data)
        self.assertTrue(form.is_valid())

    def test_validation_of_rrule_invalid(self):
        data = self.valid_form_data.copy()
        data["recurrences"] = "hello world"

        form = AgendaForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("Invalid recurrence rule", str(form.errors))

    def test_custom_error_messages(self):
        """Test that custom error messages are shown for required fields"""
        form = AgendaForm(data={"item_title": ""})
        self.assertFalse(form.is_valid())

        # Check custom error messages are set
        self.assertIn(
            "Required: Please enter the start date and time.",
            str(form.errors.get("startdatetime", [])),
        )
        self.assertIn(
            "Required: Please enter the end date and time.",
            str(form.errors.get("enddatetime", [])),
        )
        self.assertIn(
            "Required: Please enter the agenda item title.",
            str(form.errors.get("item_title", [])),
        )

    def test_form_saves_agenda_item(self):
        """Test that form creates and saves Agenda instance correctly"""
        form = AgendaForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid())

        agenda = form.save(commit=False)
        agenda.user = self.user
        agenda.save()

        self.assertEqual(agenda.item_title, "Test Agenda Item")
        self.assertEqual(agenda.startdatetime, self.valid_form_data["startdatetime"])
        self.assertEqual(agenda.user, self.user)

    def test_form_with_existing_instance(self):
        """Test form behavior when editing existing agenda item"""
        agenda = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 15, 14, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 15, 16, 0, tzinfo=timezone.utc),
            item_title="Existing Item",
            user=self.user,
        )

        form = AgendaForm(instance=agenda)
        self.assertEqual(form.instance, agenda)
        # Form overrides initial value for item_title
        self.assertEqual(form.fields["item_title"].initial, "")

    def test_form_handles_unicode_and_special_characters(self):
        """Test form properly handles international characters"""
        special_data = self.valid_form_data.copy()
        special_data.update(
            {
                "item_title": "Meeting with café ☕ discussion",
                "item_details": "Discussing αβγ international topics 中文",
            }
        )

        form = AgendaForm(data=special_data)
        self.assertTrue(form.is_valid())


class AgendaStatusFormTest(TestCase):
    """Test AgendaStatusForm business logic"""

    def setUp(self):
        self.user = User.objects.create_user(
            first_name="Status",
            last_name="User",
            password="testpassword",
            email="statususer@example.com",
        )

        self.agenda = Agenda.objects.create(
            startdatetime=datetime(2025, 5, 15, 14, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 5, 15, 16, 0, tzinfo=timezone.utc),
            item_title="Test Item",
            user=self.user,
        )

    def test_form_accepts_valid_status_choices(self):
        """Test form validates against defined status choices"""
        valid_statuses = [
            "help_wanted",
            "pending",
            "overdue",
            "in_progress",
            "completed",
            "cancelled",
            "not_done",
        ]

        for status in valid_statuses:
            form = AgendaStatusForm(data={"status": status}, instance=self.agenda)
            self.assertTrue(
                form.is_valid(),
                f"Status '{status}' should be valid, errors: {form.errors}",
            )

    def test_form_rejects_invalid_status(self):
        """Test form rejects invalid status values"""
        form = AgendaStatusForm(data={"status": "invalid_status"}, instance=self.agenda)
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)

    def test_form_requires_status_field(self):
        """Test that status field is required"""
        form = AgendaStatusForm(data={}, instance=self.agenda)
        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)

    def test_save_calls_set_status_method(self):
        """Test that save method calls agenda.set_status()"""
        form = AgendaStatusForm(data={"status": "completed"}, instance=self.agenda)
        self.assertTrue(form.is_valid())

        with patch.object(self.agenda, "set_status") as mock_set_status:
            form.save(self.user)
            mock_set_status.assert_called_once_with("completed", self.user)

    def test_save_creates_audit_trail(self):
        """Test that status changes are recorded in audit trail"""
        initial_count = AgendaChoreStatusChange.objects.count()

        form = AgendaStatusForm(data={"status": "completed"}, instance=self.agenda)
        self.assertTrue(form.is_valid())
        form.save(self.user)

        # Verify audit record was created
        self.assertEqual(AgendaChoreStatusChange.objects.count(), initial_count + 1)

        change_record = AgendaChoreStatusChange.objects.latest("created_at")
        self.assertEqual(change_record.agenda, self.agenda)
        self.assertEqual(change_record.user, self.user)
        self.assertEqual(change_record.status, "completed")

    def test_save_requires_user_parameter(self):
        """Test that save method requires user for audit purposes"""
        form = AgendaStatusForm(data={"status": "completed"}, instance=self.agenda)
        self.assertTrue(form.is_valid())

        with self.assertRaises(ValueError) as context:
            form.save(None)
        self.assertIn("user must be provided", str(context.exception))

    def test_save_prevents_duplicate_status_changes(self):
        """Test that setting same status doesn't create duplicate records"""
        # Set initial status
        self.agenda.set_status("pending", self.user)
        initial_count = AgendaChoreStatusChange.objects.count()

        # Try to set same status again
        form = AgendaStatusForm(data={"status": "pending"}, instance=self.agenda)
        self.assertTrue(form.is_valid())
        form.save(self.user)

        # Should not create new record
        self.assertEqual(AgendaChoreStatusChange.objects.count(), initial_count)

    def test_status_workflow_transitions(self):
        """Test realistic status transitions through form"""
        workflow = [
            ("help_wanted", "in_progress"),
            ("in_progress", "completed"),
        ]

        for old_status, new_status in workflow:
            # Set up initial state
            if old_status:
                self.agenda.set_status(old_status, self.user)

            # Transition to new status
            form = AgendaStatusForm(data={"status": new_status}, instance=self.agenda)
            self.assertTrue(form.is_valid())

            result = form.save(self.user)
            self.assertEqual(result.status, new_status)

    def test_form_works_with_chore_agenda_items(self):
        """Test form works correctly with chore-based agenda items"""
        chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={},
            creator=self.user,
        )

        chore_agenda = Agenda.objects.create(
            startdatetime=datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc),
            item_title="Chore Item",
            user=self.user,
            chore=chore,
        )

        form = AgendaStatusForm(data={"status": "help_wanted"}, instance=chore_agenda)
        self.assertTrue(form.is_valid())

        result = form.save(self.user)
        self.assertEqual(result.status, "help_wanted")
        self.assertEqual(result.chore, chore)
