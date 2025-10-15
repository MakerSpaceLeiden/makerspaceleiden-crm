from django.test import TestCase
from rest_framework import status

from makerspaceleiden.utils import generate_signed_url
from members.models import User


class AvatarIndexViewTests(TestCase):
    def test_index_view_requires_login(self):
        response = self.client.get("/avatar/123")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_index_view_returns_png_response(self):
        user = User.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )

        self.assertTrue(self.client.login(email=user.email, password="testpassword"))

        response = self.client.get("/avatar/123")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn("mugshot-123.png", response["Content-Disposition"])

    def test_index_view_returns_png_response_with_signed_url(self):
        user = User.objects.create_user(
            email="testuser@example.com", password="testpassword"
        )

        self.assertTrue(self.client.login(email=user.email, password="testpassword"))

        signed_image_id = generate_signed_url("123")
        response = self.client.get("/avatar/" + signed_image_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertIn("mugshot-123.png", response["Content-Disposition"])
