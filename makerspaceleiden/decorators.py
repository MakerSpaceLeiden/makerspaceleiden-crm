import logging
import re
from functools import wraps

from django.conf import settings
from django.http import HttpResponse

HEADER = "HTTP_X_BEARER"
MODERN_HEADER = "HTTP_AUTHORIZATION"

logger = logging.getLogger(__name__)


def is_superuser_or_bearer(request):
    if not request.user.is_anonymous and request.user.is_privileged:
        return True

    if hasattr(settings, "UT_BEARER_SECRET"):
        secret = None
        # Pendantic header
        if request.META.get(HEADER):
            secret = request.META.get(HEADER)

        # Also accept a modern RFC 6750 style header.
        elif request.META.get(MODERN_HEADER):
            match = re.search(
                r"\bbearer\s+(\S+)", request.META.get(MODERN_HEADER), re.IGNORECASE
            )
            if match:
                secret = match.group(1)

        for bs in settings.UT_BEARER_SECRET.split():
            if secret == bs:
                return True
    return False


def superuser_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_anonymous and request.user.is_privileged:
            return function(request, *args, **kwargs)

        # Quell some odd 'code 400, message Bad request syntax ('tag=1-2-3-4')'
        request.POST

        # raise PermissionDenied
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    return wrap


def superuser_or_bearer_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if is_superuser_or_bearer(request):
            return function(request, *args, **kwargs)

        # Quell some odd 'code 400, message Bad request syntax ('tag=1-2-3-4')'
        request.POST

        # raise PermissionDenied
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    return wrap


def login_or_bearer_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if (
            request.user
            and not request.user.is_anonymous
            or is_superuser_or_bearer(request)
        ):
            return function(request, *args, **kwargs)

        # Quell some odd 'code 400, message Bad request syntax ('tag=1-2-3-4')'
        request.POST

        # raise PermissionDenied
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    return wrap


def user_or_kiosk_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        return function(request, *args, **kwargs)
        if request.user and type(request.user).__name__ == "User":
            return function(request, *args, **kwargs)

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        if ip == "127.0.0.1":
            return function(request, *args, **kwargs)

        # Quell some odd 'code 400, message Bad request syntax ('tag=1-2-3-4')'
        request.POST

        # raise PermissionDenied
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    return wrap


def login_or_priveleged(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_privileged and request.user.id != kwargs["src"]:
            return HttpResponse(
                "Denied - are not that user - nor are you priveleged",
                status=404,
                content_type="text/plain",
            )
        return function(request, *args, **kwargs)

    return wrap


def login_and_treasurer(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if (
            not request.user.is_anonymous
            and request.user.is_privileged
            and request.user.groups.filter(
                name=settings.PETTYCASH_TREASURER_GROUP
            ).exists()
        ):
            return function(request, *args, **kwargs)

        return HttpResponse("XS denied", status=403, content_type="text/plain")
