# Model tests for chores app
from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import Chore, ChoreNotification, ChoreVolunteer
from .factories import UserFactory


class ChoreModelTest(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_chore_creation(self):
        """Test basic chore creation"""
        chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={"min_required_people": 1},
            creator=self.user,
        )
        self.assertEqual(chore.name, "Test Chore")
        self.assertEqual(chore.description, "A test chore")
        self.assertEqual(chore.class_type, "BasicChore")
        self.assertEqual(chore.creator, self.user)

    def test_chore_str_representation(self):
        """Test string representation of chore"""
        chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={"min_required_people": 1},
            creator=self.user,
        )
        self.assertEqual(str(chore), "Test Chore")

    def test_chore_unique_name_constraint(self):
        """Test that chore names must be unique"""
        Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={"min_required_people": 1},
            creator=self.user,
        )

        with self.assertRaises(Exception):  # Should raise IntegrityError
            Chore.objects.create(
                name="Test Chore",  # Same name
                description="Another test chore",
                class_type="BasicChore",
                configuration={"min_required_people": 1},
                creator=self.user,
            )


class ChoreVolunteerModelTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={"min_required_people": 1},
            creator=self.user,
        )

    def test_chore_volunteer_creation(self):
        """Test basic chore volunteer creation"""
        volunteer = ChoreVolunteer.objects.create(
            user=self.user,
            chore=self.chore,
            timestamp=1753041600,
        )
        self.assertEqual(volunteer.user, self.user)
        self.assertEqual(volunteer.chore, self.chore)
        self.assertEqual(volunteer.timestamp, 1753041600)

    def test_chore_volunteer_properties(self):
        """Test chore volunteer properties"""
        volunteer = ChoreVolunteer.objects.create(
            user=self.user,
            chore=self.chore,
            timestamp=1753041600,
        )
        self.assertEqual(volunteer.first_name, self.user.first_name)
        self.assertEqual(volunteer.full_name, self.user.full_name)


class ChoreNotificationModelTest(TestCase):
    def setUp(self):
        self.user = self.user = UserFactory()
        self.chore = Chore.objects.create(
            name="Test Chore",
            description="A test chore",
            class_type="BasicChore",
            configuration={"min_required_people": 1},
            creator=self.user,
        )

    def test_notification_with_user_recipient(self):
        """Test notification creation with user recipient"""
        notification = ChoreNotification.objects.create(
            event_key="test-key-123",
            chore=self.chore,
            recipient_user=self.user,
        )
        self.assertEqual(notification.event_key, "test-key-123")
        self.assertEqual(notification.chore, self.chore)
        self.assertEqual(notification.recipient_user, self.user)
        self.assertIsNone(notification.recipient_other)

    def test_notification_with_email_recipient(self):
        """Test notification creation with email recipient"""
        notification = ChoreNotification.objects.create(
            event_key="test-key-456",
            chore=self.chore,
            recipient_other="test@example.com",
        )
        self.assertEqual(notification.event_key, "test-key-456")
        self.assertEqual(notification.chore, self.chore)
        self.assertIsNone(notification.recipient_user)
        self.assertEqual(notification.recipient_other, "test@example.com")

    def test_notification_validation_both_recipients(self):
        """Test that notification cannot have both user and email recipients"""
        notification = ChoreNotification(
            event_key="test-key-789",
            chore=self.chore,
            recipient_user=self.user,
            recipient_other="test@example.com",
        )
        with self.assertRaises(ValidationError):
            notification.clean()

    def test_notification_validation_no_recipients(self):
        """Test that notification must have at least one recipient"""
        notification = ChoreNotification(
            event_key="test-key-789",
            chore=self.chore,
        )
        with self.assertRaises(ValidationError):
            notification.clean()

    def test_notification_str_representation(self):
        """Test string representation of notification"""
        notification = ChoreNotification.objects.create(
            event_key="test-key-123",
            chore=self.chore,
            recipient_user=self.user,
        )
        self.assertIn("Notification to", str(notification))
        self.assertIn(self.user.full_name, str(notification))
        self.assertIn("Test Chore", str(notification))
