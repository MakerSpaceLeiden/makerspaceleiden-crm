from django.shortcuts import render
from django.urls import path

from . import views

urlpatterns = [
    path("api/v1/unknowntag", views.unknowntag, name="unknowntag"),
    path("unknowntags", views.unknowntags, name="unknowntags"),
    path(
        "addunknowntagtomember/<int:tag_id>",
        views.addunknowntagtomember,
        name="addunknowntagtomember",
    ),
    path(
        "addmembertounknowntag/<int:user_id>",
        views.addmembertounknowntag,
        name="addmembertounknowntag",
    ),
]
