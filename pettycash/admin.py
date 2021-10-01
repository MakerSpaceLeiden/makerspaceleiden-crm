from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import PettycashTransaction, PettycashBalanceCache

class PettycashTransactionAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass

class PettycashBalanceCacheAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    pass

admin.site.register(PettycashTransaction, PettycashTransactionAdmin)
admin.site.register(PettycashBalanceCache, PettycashBalanceCacheAdmin)

