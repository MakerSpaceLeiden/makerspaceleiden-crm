from django.urls import path

from . import views

urlpatterns = [
    path("", views.redir, name="spaceapi"),
    path("0.13", views.index, name="spaceapi013"),
    path("0.14", views.index, name="spaceapi014"),
    path("0.15", views.index, name="spaceapi015"),
]
