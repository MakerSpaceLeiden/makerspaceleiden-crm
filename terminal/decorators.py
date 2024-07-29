import logging
from functools import wraps

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from makerspaceleiden.utils import client_cert
from terminal.model import Terminal

logger = logging.getLogger(__name__)


def is_paired_terminal(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        client_sha = client_cert(request)
        if isinstance(client_sha, HttpResponse):
            return client_sha

        try:
            terminal = Terminal.objects.get(fingerprint=client_sha)
        except ObjectDoesNotExist:
            logger.error("Unknwon terminal; fingerprint=%s" % client_sha)
            return HttpResponse(
                "No client identifier, rejecting", status=400, content_type="text/plain"
            )

        if not terminal.accepted:
            logger.error("Terminal %s not activated; rejecting." % terminal.name)
            return HttpResponse(
                "Terminal not activated, rejecting",
                status=400,
                content_type="text/plain",
            )
        # if not request.user.is_anonymous and request.user.is_privileged:
        #  return function(request, *args, **kwargs)

        return function(request, terminal, *args, **kwargs)

    return wrap
