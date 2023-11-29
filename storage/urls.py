from django.conf import settings
from django.urls import path, re_path

from . import views

if not settings.STORAGE:
    urlpatterns = [re_path(r".*", views.nope)]
else:
    urlpatterns = [
        path("", views.index, {"user_pk": None}, name="storage"),
        path("<int:user_pk>", views.index, name="storage"),
        path("add", views.create, name="addstorage"),
        path("show/<int:pk>", views.showstorage, name="showstorage"),
        path("modify/<int:pk>", views.modify, name="changestorage"),
        path("delete/<int:pk>", views.delete, name="deletestorage"),
        path("showhistory/<int:pk>", views.showhistory, name="showhistory"),
        path("showhistory/<int:pk>/<int:rev>", views.showhistory, name="showhistory"),
    ]
