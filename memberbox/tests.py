# Create your tests here.

from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from members.models import User


class MemberboxSanityTest(TestCase):
    """High-level sanity tests to validate 200 responses for memberbox app endpoints."""

    def setUp(self):
        """Set up test client and create a test user."""
        self.client = Client()
        # Create a test user for authenticated endpoints
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            telegram_user_id="123456789",
        )
        self.email = "test@example.com"
        self.password = "testpass123"

    def test_boxes_index_authenticated(self):
        """Test that the main boxes index page returns 200 for authenticated users."""
        self.client.login(email=self.email, password=self.password)

        response = self.client.get("/boxes/")

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertIn("Member boxes", response.content.decode("utf-8"))
        self.assertIn("user", response.context)

    def test_boxes_index_unauthenticated(self):
        """Test that the main boxes index page redirects unauthenticated users."""
        response = self.client.get("/boxes/")

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_add_box_authenticated(self):
        """Test that the add box page returns 200 for authenticated users."""
        self.client.login(email=self.email, password=self.password)

        response = self.client.get("/boxes/add")

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertIn("Create Memberbox", response.content.decode("utf-8"))

    def test_add_box_unauthenticated(self):
        """Test that the add box page redirects unauthenticated users."""
        response = self.client.get("/boxes/add")

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_claim_box_authenticated(self):
        """Test that the claim box page returns 200 for authenticated users."""
        self.client.login(email=self.email, password=self.password)

        response = self.client.get("/boxes/claim/A1")

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertIn("Create Memberbox", response.content.decode("utf-8"))

    def test_claim_box_unauthenticated(self):
        """Test that the claim box page redirects unauthenticated users."""
        response = self.client.get("/boxes/claim/A1")

        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_patterns(self):
        """Test that all URL patterns are properly configured."""
        try:
            boxes_url = reverse("boxes")
            self.assertEqual(boxes_url, "/boxes/")
        except Exception as e:
            self.fail(f"URL reverse lookup failed for 'boxes': {e}")

        try:
            addbox_url = reverse("addbox")
            self.assertEqual(addbox_url, "/boxes/add")
        except Exception as e:
            self.fail(f"URL reverse lookup failed for 'addbox': {e}")
