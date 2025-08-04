import logging

from oauth2_provider.oauth2_validators import OAuth2Validator

logger = logging.getLogger(__name__)

logger.info("makerspaceleiden.customoauth2validator")


class CustomOAuth2Validator(OAuth2Validator):
    def validate_code(self, client_id, code, client, request, *args, **kwargs):
        """
        Called during authorization code exchange for access token.
        This is where we check permissions for authorization code flow.
        """
        logger.info(f"Validating code for client: {client_id}")
        print("CUSTOM VALIDATE CODE CALLED")
        # First let parent validate the authorization code
        is_valid = super().validate_code(
            client_id, code, client, request, *args, **kwargs
        )

        if not is_valid:
            logger.info("Parent validation failed")
            return False

        if hasattr(request, "user"):
            logger.info("Checking user permission?")
            if not request.user.has_perm("members.wiki_account"):
                logger.info("User does not have necessary permission")
                return False

        return is_valid

    def get_additional_claims(self, request):
        preferred_name = " ".join([request.user.first_name, request.user.last_name])
        return {
            "given_name": request.user.first_name,
            "family_name": request.user.last_name,
            "name": preferred_name,
            "preferred_username": preferred_name,
            "email": request.user.email,
        }

    def get_userinfo_claims(self, request):
        claims = super().get_userinfo_claims(request)

        preferred_name = " ".join([request.user.first_name, request.user.last_name])
        claims["name"] = preferred_name
        claims["preferred_name"] = preferred_name
        return claims
