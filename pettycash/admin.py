from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from django.contrib import admin

from .models import PettycashTransaction, PettycashBalanceCache, PettycashSku

class PettycashTransactionAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('date', 'dst', 'src', 'amount', 'description')
    pass

class PettycashBalanceCacheAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('owner','balance','last')
    pass

class PettycashSkuAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('pk', 'name','amount','description')
    pass

admin.site.register(PettycashTransaction, PettycashTransactionAdmin)
admin.site.register(PettycashBalanceCache, PettycashBalanceCacheAdmin)
admin.site.register(PettycashSku, PettycashSkuAdmin)
