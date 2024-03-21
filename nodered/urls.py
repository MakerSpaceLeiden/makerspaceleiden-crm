from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^nodered/(?P<url>.*)$", views.NodeRedProxy.as_view(), name="proxy")
]
