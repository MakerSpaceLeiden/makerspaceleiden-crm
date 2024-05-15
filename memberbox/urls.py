from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="boxes"),
    path("add", views.create, name="addbox"),
    path("claim/<str:location>", views.claim, name="claim"),
    path("modify/<int:pk>", views.modify, name="changebox"),
    path("delete/<int:pk>", views.delete, name="deletebox"),
]
