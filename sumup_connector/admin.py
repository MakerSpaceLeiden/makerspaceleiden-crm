import json

from django.contrib import admin
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Checkout


class CheckoutAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    readonly_fields = [
        "extra_information",
        "date",
        "member",
        "amount",
        "terminal",
        "client_transaction_id",
        "transaction_id",
        "transaction_date",
        "settled_tx",
        "fee_tx",
    ]

    # history_list_display = ["changed_fields","list_changes"]
    history_list_display = ["list_changes"]

    def format_html_json(self, val):
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                pass
        if isinstance(val, dict):
            val = json.dumps(val, sort_keys=True, indent=4)
        return f"<pre>{val}</pre>".replace("{", "&#123;").replace("}", "&#124;")

    def extra_information(self, instance):
        return format_html(self.format_html_json(instance.debug_note))

    def changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return delta.changed_fields
        return None

    def list_changes(self, obj):
        fields = "New values<p/>"
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)

            for change in delta.changes:
                # fields += "<strong>{}</strong> changed from <span style='background-color:#ffb5ad'>{}</span> to <span style='background-color:#b3f7ab'>{}</span>.<br/>".format(change.field, self.format_html_json(change.old), self.format_html_json(change.new))
                fields += "<strong>{}</strong>: <span style='background-color:#b3f7ab'>{}</span>.<br/>".format(
                    change.field, self.format_html_json(change.new)
                )
            print(f"\n{fields}\n")
            return format_html(fields)
        return None


admin.site.register(Checkout, CheckoutAdmin)
