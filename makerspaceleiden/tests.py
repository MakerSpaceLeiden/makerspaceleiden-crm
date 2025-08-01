from http import HTTPStatus

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from oauth2_provider.models import Application

from makerspaceleiden.utils import derive_initials
from members.models import User


class MakerspaceleidenTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(
            "Intranet – " + settings.SITE_NAME, response.content.decode("utf-8")
        )

    @pytest.mark.django_db
    def test_login(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(
            "<title>Login – " + settings.SITE_NAME + "</title>",
            response.content.decode("utf-8"),
        )


class DeriveInitialsTest(TestCase):
    def test_derive_initials_cases(self):
        cases = [
            (("Abd", "al-Ghazali"), "AG"),
            (("Abd", "Al-Ghazali"), "AG"),
            (("Abd", "al Ghazali"), "AG"),
            (("Sara", "el-Ghazali"), "SG"),
            (("Sara", "El Ghazali"), "SG"),
            (("John", "Doe"), "JD"),
            (("Anna", "Smith"), "AS"),
            (("Jan", "van de Smith"), "JS"),
            (("Piet", "Van Vliet"), "PV"),
            (("Kees", "de Groot"), "KG"),
            (("Sanne", "van der Meer"), "SM"),
            (("Lotte", "ten Brink"), "LB"),
            (("Cher", ""), "C"),
            (("", "Madonna"), "M"),
            (("Hy-Phenated", "Name"), "HN"),
        ]
        for (first, last), expected in cases:
            with self.subTest(first_name=first, last_name=last):
                self.assertEqual(derive_initials(first, last), expected)


class OAuth2IntegrationTest(TestCase):
    """Integration tests using django-oauth-toolkit's test client."""

    def setUp(self):
        self.user_with_permission = User.objects.create_user(
            first_name="Model",
            last_name="Test",
            email="authorized_user.oauth@example.com",
            password="testpass123",
        )

        self.user_without_permission = User.objects.create_user(
            first_name="Model",
            last_name="Test",
            password="testpass123",
            email="unauthorized_user.oauth@example.com",
        )

        # Get the existing permission (it should already exist from migrations)
        oauth_permission = Permission.objects.get(codename="wiki_account")
        self.user_with_permission.user_permissions.add(oauth_permission)

        # Create OAuth2 application
        self.application = Application.objects.create(
            name="Test App",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_PASSWORD,
        )

    def test_oauth2_openid_configuration_available(self):
        with override_settings(
            OAUTH2_PROVIDER={
                "OIDC_ENABLED": True,
            }
        ):
            response = self.client.get("/oauth2/.well-known/openid-configuration")
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_token_request_with_permission_succeeds(self):
        """Test full OAuth2 token request with authorized user."""

        with override_settings(
            OAUTH2_PROVIDER={
                "OIDC_ENABLED": True,
                "OAUTH2_VALIDATOR_CLASS": "makerspaceleiden.oauth_validators.CustomOAuth2Validator",
            }
        ):
            success = self.client.login(
                email=self.user_with_permission.email,
                password="testpass123",
            )
            self.assertTrue(success)
            response = self.client.post(
                "/oauth2/token/",
                {
                    "grant_type": "password",
                    "email": self.user_with_permission.email,
                    "password": "testpass123",
                    "client_id": self.application.client_id,
                    "client_secret": self.application.client_secret,
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIn("access_token", response.json())
            self.assertIn("token_type", response.json())

    # def test_token_request_without_permission_fails(self):
    #     """Test full OAuth2 token request with unauthorized user."""
    #     response = self.client.post(
    #         "/o/token/",
    #         {
    #             "grant_type": "password",
    #             "email": self.user_without_permission.email,
    #             "password": "testpass123",
    #             "client_id": self.application.client_id,
    #             "client_secret": self.application.client_secret,
    #         },
    #     )

    #     self.assertEqual(response.status_code, 400)
    #     response_data = response.json()
    #     self.assertEqual(response_data["error"], "invalid_grant")

    # def test_token_request_invalid_credentials_fails(self):
    #     """Test token request with wrong password."""
    #     response = self.client.post(
    #         "/o/token/",
    #         {
    #             "grant_type": "password",
    #             "username": self.user_with_permission.email,
    #             "password": "wrongpassword",
    #             "client_id": self.application.client_id,
    #             "client_secret": self.application.client_secret,
    #         },
    #     )

    #     self.assertEqual(response.status_code, 400)
    #     response_data = response.json()
    #     self.assertEqual(response_data["error"], "invalid_grant")
