from django.urls import path

from . import views

urlpatterns = [
    path("", views.redir, name="spaceapi"),
    path("0.13", views.index, name="spaceapi013"),
]
