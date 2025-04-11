from functools import update_wrapper

from django.contrib import admin
from django.contrib.admin.utils import quote
from django.contrib.admin.views.main import ChangeList
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from simple_history.admin import SimpleHistoryAdmin

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

    _ = {
        "title": "View history",
    }

    if not cacheable:
        inner = never_cache(inner)

    # We add csrf_protect here so this function can be used as a utility
    # function for any view, without having to repeat 'csrf_protect'.
    if not getattr(view, "csrf_exempt", False):
        inner = csrf_protect(inner)

    return update_wrapper(inner, view)


class SimpleHistoryShowDeletedFilter(admin.SimpleListFilter):
    title = "Entries"
    parameter_name = "entries"

    def lookups(self, request, model_admin):
        return (("deleted_only", "Only Deleted"),)

    def queryset(self, request, queryset):
        if self.value():
            return queryset.model.history.filter(history_type="-").distinct()
        return queryset


class SimpleHistoryChangeList(ChangeList):
    def apply_select_related(self, qs):
        # Our qs is different if we use the history, so the normal select_related
        # won't work and results in an empty QuerySet result.
        history = self.params.get("entries", None) == "deleted_only"
        if history:
            return qs
        return super().apply_select_related(qs)

    def url_for_result(self, result) -> str:
        history = self.params.get("entries", None) == "deleted_only"
        route_type = "history" if history else "change"
        route = f"{self.opts.app_label}_{self.opts.model_name}_{route_type}"
        pk = getattr(result, self.pk_attname)
        return reverse(
            f"admin:{route}",
            args=(quote(pk),),
            current_app=self.model_admin.admin_site.name,
        )


class SimpleHistoryWithDeletedAdmin(SimpleHistoryAdmin):
    def get_changelist(self, request, **kwargs):
        return SimpleHistoryChangeList

    def get_list_filter(self, request):
        # Doing it here will add it to every inherited class. Alternatively,
        # add SimpleHistoryShowDeletedFilter to the list_filter and remove the below.
        return [SimpleHistoryShowDeletedFilter] + [
            f for f in super().get_list_filter(request)
        ]
