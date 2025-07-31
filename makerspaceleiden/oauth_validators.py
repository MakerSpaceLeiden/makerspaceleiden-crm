import logging

from django.contrib.auth import authenticate
from oauth2_provider.oauth2_validators import OAuth2Validator

logger = logging.getLogger(__name__)


class CustomOAuth2Validator(OAuth2Validator):
    # Set `oidc_claim_scope = None` to ignore scopes that limit which claims to return,
    # otherwise the OIDC standard scopes are used.
    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        Check custom permissions first, then delegate to parent for standard validation.
        Returns False if user doesn't have required permission, blocking the login.
        """
        # First authenticate the user to check permissions
        user = authenticate(username=username, password=password)

        # If authentication failed, return False immediately
        if not user or not user.is_active:
            logger.info("failed to find user")
            return False

        # Check if user has the required permission before proceeding
        if not user.has_perm("members.wiki_account"):
            # Permission check failed - block the login
            logger.info("user does not have necessary permission")
            return False

        return super().validate_user(
            username, password, client, request, *args, **kwargs
        )

    def get_additional_claims(self, request):
        return {
            "given_name": request.user.first_name,
            "family_name": request.user.last_name,
            "name": " ".join([request.user.first_name, request.user.last_name]),
            "preferred_username": request.user.username,
            "email": request.user.email,
        }
