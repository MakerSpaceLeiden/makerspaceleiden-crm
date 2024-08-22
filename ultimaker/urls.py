from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="camindex"),
    path("snapshot", views.snapshot, name="snapshot"),
]
