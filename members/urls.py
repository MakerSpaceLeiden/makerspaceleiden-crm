from django.urls import path
from django.conf import settings

from . import views

urlpatterns = [
    path("", views.index, name="members-index"),
    path("newmember", views.newmember, name="newmember"),
    path("sudo", views.sudo, name="sudo"),
    path("drop", views.drop, name="drop"),
]
