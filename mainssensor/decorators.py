from functools import wraps

from django.conf import settings
from django.http import HttpResponse


def superuser_or_mainsadmin_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user:
            if (
                request.user.is_privileged
                or request.user.groups.filter(name=settings.SENSOR_USER_GROUP).exists()
            ):
                return function(request, *args, **kwargs)
        return HttpResponse("XS denied", status=403, content_type="text/plain")

    return wrap
