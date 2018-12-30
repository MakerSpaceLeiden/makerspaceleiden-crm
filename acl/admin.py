from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from import_export import resources

from django.utils.translation import ugettext_lazy as _

from members.models import User
from .models import PermitType
from .models import Machine
from .models import Location
from .models import Entitlement

#class MachineAdmin(ImportExportModelAdmin,admin.ModelAdmin):
class MachineAdmin(ImportExportModelAdmin,SimpleHistoryAdmin):
    list_display = ('name','description','location','requires_instruction','requires_form','requires_permit')
admin.site.register(Machine,MachineAdmin)

#class LocationAdmin(ImportExportModelAdmin,admin.ModelAdmin):
class LocationAdmin(ImportExportModelAdmin,SimpleHistoryAdmin):
    list_display = ('name','description')
admin.site.register(Location,LocationAdmin)

class EntitlementResource(resources.ModelResource):
    class Meta:
       model = Entitlement
       fields = [ 'permit', 'holder', 'issuer' ]
       import_id_fields = [ 'permit', 'holder', 'issuer' ]
       # import_id_fields = [ 'permit', 'holder', 'issuer' ]

class EntitlementAdmin(ImportExportModelAdmin,SimpleHistoryAdmin):
    list_display = ('permit','holder','issuer')
    resource_class = EntitlementResource
admin.site.register(Entitlement,EntitlementAdmin)

class PermitAdmin(ImportExportModelAdmin,SimpleHistoryAdmin):
    list_display = ('name','description')
admin.site.register(PermitType,PermitAdmin)

