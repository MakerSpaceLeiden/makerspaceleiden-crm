from django.urls import path

from agenda.views import (
    AgendaCreateView,
    AgendaDeleteView,
    AgendaItemsView,
    AgendaUpdateView,
)

urlpatterns = [
    path("agenda/", AgendaItemsView, name="agenda"),
    path("agenda/<int:pk>/", AgendaItemsView, name="agenda_detail"),
    path("agenda/<int:pk>/update/", AgendaUpdateView, name="agenda_update"),
    path("agenda/<int:pk>/delete/", AgendaDeleteView, name="agenda_delete"),
    path("agenda_create/", AgendaCreateView, name="agenda_create"),
]
