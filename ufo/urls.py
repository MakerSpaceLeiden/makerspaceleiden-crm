from django.urls import path
from . import views

urlpatterns = [
    path("<int:days>", views.index, name="ufo"),
    path("", views.index, name="ufo"),
    path("add", views.create, name="addufo"),
    path("show/<int:pk>", views.show, name="showufo"),
    path("modify/<int:pk>", views.modify, name="changeufo"),
    path("delete/<int:pk>", views.delete, name="deleteufo"),
    path("mine/<int:pk>", views.mine, name="mine"),
    path("upload", views.upload_zip, name="uploadufo"),
]
