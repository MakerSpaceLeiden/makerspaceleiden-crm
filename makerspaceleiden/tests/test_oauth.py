import urllib.parse as urlparse
from http import HTTPStatus

from django.test import TestCase, override_settings
from django.urls import reverse
from oauth2_provider.models import Application, get_application_model

from acl.models import Entitlement, PermitType
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
        admin = User.objects.create_superuser(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="testpass123",
        )
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        self.admin = admin

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

        # Create a new PermitType
        permit = PermitType.objects.create(
            name="wiki account",
            description="Wiki account",
            require_ok_trustee=False,
            permit=None,
        )

        # Create a new Entitlement
        Entitlement.objects.create(
            holder=self.user_with_permission,
            permit=permit,
            active=True,
            issuer=admin,
        )

        # Create OAuth2 application
        self.client_secret = "plaintextsecret"
        self.application = get_application_model().objects.create(
            name="Test App",
            client_type=Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
            client_secret=self.client_secret,
            redirect_uris="http://testserver/callback",
            permit=permit,
        )

    def test_oauth2_openid_configuration_available(self):
        with override_settings(
            OAUTH2_PROVIDER=oauth_settings,
        ):
            response = self.client.get(
                reverse("oauth2_provider:oidc-connect-discovery-info")
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def _auth_flow(self, application):
        # Get the authorization code
        response = self.client.post(
            reverse("oauth2_provider:token"),
            {
                "client_id": application.client_id,
                "response_type": "code",
                "redirect_uri": application.redirect_uris,
                "state": "random_state_string",
                "scope": "read",
            },
        )

        # User submits authorization form (simulate approval)
        response = self.client.post(
            reverse("oauth2_provider:authorize"),
            data={
                "client_id": application.client_id,
                "response_type": "code",
                "redirect_uri": "http://testserver/callback",
                "scope": "read",
                "state": "random_state_string",
                "allow": True,
            },
        )

        # Step 2: Exchange code for token
        token_response = self.client.post(
            reverse("oauth2_provider:token"),
            data={
                "grant_type": "authorization_code",
                "code": get_code_from_response(response),
                "redirect_uri": "http://testserver/callback",
                "client_id": application.client_id,
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

            token_response = self._auth_flow(self.application)

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

            response = self._auth_flow(self.application)

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            response_data = response.json()
            self.assertEqual(response_data["error"], "invalid_grant")
