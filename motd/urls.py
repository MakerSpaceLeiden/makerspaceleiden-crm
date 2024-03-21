from django.urls import path

from . import views

urlpatterns = [
    path("motd", views.motd, name="motd"),
]
