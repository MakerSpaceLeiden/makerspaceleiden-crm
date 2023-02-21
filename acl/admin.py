from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from import_export import resources
from django.conf import settings

from django.utils.translation import gettext_lazy as _

from members.models import User
from .models import PermitType
from .models import Machine
from .models import Location
from .models import Entitlement
from .models import RecentUse


# class MachineAdmin(ImportExportModelAdmin,admin.ModelAdmin):
class MachineAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = (
        "name",
        "node_name",
        "node_machine_name",
        "description",
        "location",
        "requires_instruction",
        "requires_form",
        "requires_permit",
    )


admin.site.register(Machine, MachineAdmin)


# class LocationAdmin(ImportExportModelAdmin,admin.ModelAdmin):
class LocationAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("name", "description")


admin.site.register(Location, LocationAdmin)


class EntitlementResource(resources.ModelResource):
    class Meta:
        model = Entitlement
        fields = ["permit", "holder", "issuer", "active"]
        import_id_fields = ["permit", "holder", "issuer"]
        # import_id_fields = [ 'permit', 'holder', 'issuer' ]


class EntitlementAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("permit", "holder", "issuer", "active")
    resource_class = EntitlementResource
    search_fields = [
        "permit__name",
        "holder__first_name",
        "holder__last_name",
        "holder__email",
    ]

    def get_changeform_initial_data(self, request):
        defaults = {"active": True, "issuer": request.user, "permit": settings.DOORS}

        # See if there is a user which does not yet have a door permit; and the the
        # one with the highest user id.
        #
        nodoors = (
            User.objects.all().exclude(isGivenTo__permit=settings.DOORS).order_by("-id")
        )
        if nodoors:
            defaults["holder"] = nodoors[0]

        return defaults


admin.site.register(Entitlement, EntitlementAdmin)


class PermitAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("name", "description", "require_ok_trustee", "permit")


admin.site.register(PermitType, PermitAdmin)


class RecentUseAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("user", "machine", "used")


admin.site.register(RecentUse, RecentUseAdmin)
