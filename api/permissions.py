from rest_framework.permissions import DjangoModelPermissions
from rest_framework_api_key.permissions import HasAPIKey


class DjangoModelOrApiKeyPermission:
    """
    Permission that allows access if EITHER DjangoModelPermissions OR HasAPIKey is granted.
    """

    def has_permission(self, request, view):
        return DjangoModelPermissions().has_permission(
            request, view
        ) or HasAPIKey().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        return DjangoModelPermissions().has_object_permission(
            request, view, obj
        ) or HasAPIKey().has_object_permission(request, view, obj)
