from django.urls import path

from agenda.views import (
    AgendaCreateView,
    AgendaDeleteView,
    AgendaItemDetailView,
    AgendaItemsView,
    AgendaUpdateView,
)

urlpatterns = [
    path("agenda/", AgendaItemsView, name="agenda"),
    path("agenda/<int:pk>/", AgendaItemDetailView, name="agenda_detail"),
    path("agenda/<int:pk>/update/", AgendaUpdateView, name="agenda_update"),
    path("agenda/<int:pk>/delete/", AgendaDeleteView, name="agenda_delete"),
    path("agenda/create/", AgendaCreateView, name="agenda_create"),
]
