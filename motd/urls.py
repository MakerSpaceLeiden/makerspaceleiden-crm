from django.urls import path

from motd.views import (
    MotdCreateView,
    MotdDeleteView,
    MotdMessagesView,
    MotdUpdateView,
    MotdView,
)

urlpatterns = [
    path("motd/", MotdView, name="motd"),
    path("motd_messages/", MotdMessagesView, name="motd_messages"),
    path("motd_messages/<int:pk>/", MotdMessagesView, name="motd_messages_detail"),
    path("motd/<int:pk>/update/", MotdUpdateView, name="motd_update"),
    path("motd/<int:pk>/delete/", MotdDeleteView, name="motd_delete"),
    path("motd_create/", MotdCreateView, name="motd_create"),
]
