from django.urls import path

from . import views

urlpatterns = [
    path(
        "crud/<int:machine_id>/<int:servicelog_id>",
        views.servicelog_crud,
        name="service_log_crud",
    ),
    path("crud/<int:machine_id>", views.servicelog_crud, name="service_log_crud"),
    path("<int:machine_id>", views.servicelog_overview, name="service_log_view"),
    path("", views.servicelog_overview, name="service_log"),
]
