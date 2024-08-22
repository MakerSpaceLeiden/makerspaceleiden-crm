from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="members-index"),
    path("newmember", views.newmember, name="newmember"),
    path("sudo", views.sudo, name="sudo"),
    path("drop", views.drop, name="drop"),
]
