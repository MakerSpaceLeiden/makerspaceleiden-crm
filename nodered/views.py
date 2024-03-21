import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from djproxy.views import HttpProxy

logger = logging.getLogger(__name__)


class NodeRedProxy(HttpProxy):
    base_url = settings.NODERED_URL

    def dispatch(self, request, *args, **kwargs):
        #  Using rest auth outside of the rest framework requires a manual check
        try:
            if not request.user.is_anonymous and request.user.is_privileged:
                logger.warning("User is not logged in and cannot access nodered")
                raise ObjectDoesNotExist()

            return super().dispatch(request, *args, **kwargs)
        except ObjectDoesNotExist:
            redirect("overview")
