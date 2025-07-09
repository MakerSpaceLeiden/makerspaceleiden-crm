from django.urls import path

from . import views

urlpatterns = [
    path("<int:pk>", views.index, name="generate-fake-mugshot"),
]

