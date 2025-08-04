from http import HTTPStatus

import pytest
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from oauth2_provider.models import Application, get_application_model
import urllib.parse as urlparse

from members.models import User

# Extract code from redirect URL
def get_code_from_response(response):
    redirect_url = response["Location"]
           
    query = urlparse.urlparse(redirect_url).query
    params = urlparse.parse_qs(query)
    return params["code"][0]


oauth_settings = {
    "OIDC_ENABLED": True,
    "OAUTH2_VALIDATOR_CLASS": "makerspaceleiden.oauth_validators.CustomOAuth2Validator",
    "PKCE_REQUIRED": False,
}

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
        self.client_secret = "plaintextsecret"
        self.application = get_application_model().objects.create(
            name="Test App",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_secret=self.client_secret,
            redirect_uris="http://testserver/callback",
        )

    def test_oauth2_openid_configuration_available(self):
        with override_settings(
            OAUTH2_PROVIDER=oauth_settings,
        ):
            response = self.client.get("/oauth2/.well-known/openid-configuration")
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def _auth_flow(self):
        # Get the authorization code
        response = self.client.post(
            "/oauth2/authorize/",
            {
                "client_id": self.application.client_id,
                "response_type": "code",
                "redirect_uri": self.application.redirect_uris,
                "state": "random_state_string",
                "scope": "read",
            },
        )

        # User submits authorization form (simulate approval)
        response = self.client.post(
            "/oauth2/authorize/",
            data={
                "client_id": self.application.client_id,
                "response_type": "code",
                "redirect_uri": "http://testserver/callback",
                "scope": "read",
                "state": "random_state_string",
                "allow": True,
            },
        )

        # Step 2: Exchange code for token
        token_response = self.client.post(
            "/oauth2/token/",
            data={
                "grant_type": "authorization_code",
                "code": get_code_from_response(response),
                "redirect_uri": "http://testserver/callback",
                "client_id": self.application.client_id,
                "client_secret": self.client_secret,  # Use plaintext secret in tests
            },
        )

        return token_response

    def test_token_request_with_permission_succeeds(self):
        """Test full OAuth2 token request with authorized user."""

        with override_settings(
            OAUTH2_PROVIDER=oauth_settings,
        ):
            success = self.client.login(
                email=self.user_with_permission.email,
                password="testpass123",
            )
            self.assertTrue(success)

            token_response = self._auth_flow()

            self.assertEqual(token_response.status_code, HTTPStatus.OK)
            json_response = token_response.json()
            self.assertIn("access_token", json_response)

    def test_token_request_without_permission_fails(self):
        """Test full OAuth2 token request with unauthorized user."""

        with override_settings(
            OAUTH2_PROVIDER=oauth_settings,
        ):
            success = self.client.login(
                email=self.user_without_permission.email,
                password="testpass123",
            )
            self.assertTrue(success)

            response = self._auth_flow()

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            response_data = response.json()
            self.assertEqual(response_data["error"], "invalid_grant")