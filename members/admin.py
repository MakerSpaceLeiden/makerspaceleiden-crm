from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from makerspaceleiden.admin import SimpleHistoryWithDeletedAdmin
from search_admin_autocomplete.admin import SearchAutoCompleteAdmin

from .models import AuditRecord, Tag, User


class UserResource(resources.ModelResource):
    full_name = fields.Field(column_name="Full Name")

    def dehydrate_full_name(self, obj):
        return "%s %s" % (obj.first_name, obj.last_name)

    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "date_joined",
            "form_on_file",
            "email_confirmed",
        )
        import_id_fields = ["first_name", "last_name", "email"]


class TagResource(resources.ModelResource):
    class Meta:
        model = Tag
        fields = ["owner", "tag"]
        import_id_fields = ["owner", "tag"]


class UserAdmin(
    ImportExportModelAdmin,
    SearchAutoCompleteAdmin,
    BaseUserAdmin,
    SimpleHistoryWithDeletedAdmin,
):
    resource_class = UserResource
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Membership"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "image",
                    "phone_number",
                    "form_on_file",
                    "email_confirmed",
                )
            },
        ),
        (_("BOTs"), {"fields": ("telegram_user_id", "uses_signal")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    list_display = (
        "email",
        "first_name",
        "last_name",
        "form_on_file",
        "last_login",
        "date_joined",
    )
    search_fields = ["email", "first_name", "last_name"]
    ordering = ("email", "first_name", "last_name")
    import_id_fields = ()  # 'email', 'first_name', 'last_name', 'is_staff', 'form_on_file', 'last_login','date_joined')


admin.site.register(User, UserAdmin)


class TagAdmin(ImportExportModelAdmin, SimpleHistoryAdmin, SearchAutoCompleteAdmin):
    list_display = ("tag", "owner", "last_used", "description")
    resource_class = TagResource
    search_fields = ["tag", "owner__first_name", "owner__last_name", "owner__email"]


admin.site.register(Tag, TagAdmin)


class AuditRecordAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ("user", "action", "recorded")
    resource_class = AuditRecord


admin.site.register(AuditRecord, AuditRecordAdmin)
