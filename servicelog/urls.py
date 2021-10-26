from django.urls import path
from django.contrib.auth import views as auth_views

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
