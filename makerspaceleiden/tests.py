from http import HTTPStatus
from unittest import TestCase

from django.conf import settings
from django.test import Client, override_settings


class MakerspaceleidenTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(
            "Intranet – " + settings.SITE_NAME, response.content.decode("utf-8")
        )

    def test_login(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(
            "<title>Login – " + settings.SITE_NAME + "</title>",
            response.content.decode("utf-8"),
        )


    def test_oauth2_openid_configuration_available(self):
        with override_settings(
            OAUTH2_PROVIDER={
                "OIDC_ENABLED": True,
            }
        ):
            response = self.client.get("/oauth2/.well-known/openid-configuration")
            self.assertEqual(response.status_code, HTTPStatus.OK)
