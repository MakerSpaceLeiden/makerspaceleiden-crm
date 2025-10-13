import logging

from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from acl.models import Machine
from pettycash.models import PettycashStation

from .models import Terminal

logger = logging.getLogger(__name__)


@admin.register(Terminal)
class TerminalAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("pk", "accepted", "date", "used_at", "name", "fingerprint")
    readonly_fields = ["fingerprint", "nonce", "date", "used_at"]

    def used_at(self, terminal):
        used = []
        try:
            for s in PettycashStation.objects.all().filter(terminal_id=terminal.id):
                used.append(s)
        except ObjectDoesNotExist:
            pass

        try:
            for n in Machine.objects.all().filter(node_name=terminal.name):
                used.append(n)
        except ObjectDoesNotExist:
            pass

        if used:
            out = ""
            for obj in used:
                url = reverse(
                    "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name),
                    args=[obj.id],
                )
                out = out + f"<a href='{url}'>{obj.description}</a></br>"
            return format_html(out)
        return "--"
