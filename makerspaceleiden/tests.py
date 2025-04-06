from unittest import TestCase

from django.conf import settings
from django.test import Client


class MakerspaceleidenTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Intranet – " + settings.SITE_NAME, response.content.decode("utf-8")
        )

    def test_login(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "<title>Login – " + settings.SITE_NAME + "</title>",
            response.content.decode("utf-8"),
        )
