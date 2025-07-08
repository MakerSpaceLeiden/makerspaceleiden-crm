from django.urls import include, re_path
from rest_framework import routers

from .views import MachineViewSet, UserViewSet

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r"members", UserViewSet)
router.register(r"machines", MachineViewSet)

urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
