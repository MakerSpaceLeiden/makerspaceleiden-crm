from django.urls import path

from . import views

urlpatterns = [
    path("motd", views.motd, name="motd"),
    path("motd.json", views.motd_as_json, name="motd_js"),
]
