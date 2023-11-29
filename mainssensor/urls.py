from django.urls import path

from . import views

urlpatterns = [
    path("api/v1/mainssensor/resolve/<int:tag>", views.resolve, name="resolve"),
    path("api/v1/mainssensor/resolve", views.resolve, name="resolve"),
    path("mainsensors", views.index, name="mainsindex"),
    path("mainsensors/add", views.create, name="addsensor"),
    path("mainsensors/modify/<int:pk>", views.modify, name="changesensor"),
    path("mainsensors/delete/<int:pk>", views.delete, name="deletesensor"),
]
