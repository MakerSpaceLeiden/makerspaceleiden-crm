from functools import update_wrapper

from django.http import Http404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse

from acl.models import EntitlementViolation


def admin_view(view, cacheable=False):
    def inner(request, *args, **kwargs):
        if not request.user.is_active and not request.user.is_staff:
            raise Http404()

        if not request.user.is_anonymous and request.user.can_escalate_to_priveleged:
            if not request.user.is_privileged:
                return redirect("sudo")

        try:
            return view(request, *args, **kwargs)
        except EntitlementViolation:
            return HttpResponse(
                "Not permitted to do that", status=404, content_type="text/plain"
            )

    context = {
        "title": "View history",
    }

    if not cacheable:
        inner = never_cache(inner)

    # We add csrf_protect here so this function can be used as a utility
    # function for any view, without having to repeat 'csrf_protect'.
    if not getattr(view, "csrf_exempt", False):
        inner = csrf_protect(inner)

    return update_wrapper(inner, view)
