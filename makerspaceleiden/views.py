import logging

from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.static import serve as static_serve
from simple_history.admin import SimpleHistoryAdmin

from .decorators import login_or_bearer_required

from storage.forms import StorageForm
from storage.models import Storage

logger = logging.getLogger(__name__)


class MySimpleHistoryAdmin(SimpleHistoryAdmin):
    object_history_template = "object_history.html"

    # Bit risky - routes in to bypass for naughtyness in below showhistory.
    #
    def has_change_permission(self, request, obj):
        return True

@login_or_bearer_required
def protected_media(request,path):
    return static_serve(request,path,settings.MEDIA_ROOT)

@login_required
def showhistory(request, aClass, pk, rev=None):
    try:
        o = aClass.objects.get(pk=pk)
    except o.DoesNotExist:
        return HttpResponse(
            "History not found", pk, status=404, content_type="text/plain"
        )
    context = {
        "title": "View history",
    }
    if rev:
        revInfo = o.history.get(pk=rev)
        historic = revInfo.instance
        form = StorageForm(instance=historic)
        context = {
            "title": "Historic record",
            "label": revInfo,
            "action": None,
            "is_logged_in": request.user.is_authenticated,
            "user": request.user,
            "form": form,
            "storage": historic,
            "history": True,
            "item": o,
            "back": f"{o.__class__.__name__}_overview",
            "has_permission": request.user.is_authenticated,
        }
        return render(request, "crud.html", context)

    historyAdmin = MySimpleHistoryAdmin(Storage, AdminSite())
    return historyAdmin.history_view(request, str(pk), context)
