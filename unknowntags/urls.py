from django.urls import path

from . import views

urlpatterns = [
    path("api/v1/unknowntag", views.unknowntag, name="unknowntag"),
    path("unknowntags", views.unknowntags, name="unknowntags"),
    path(
        "addunknowntagtomember/<int:tag_id>",
        views.addunknowntagtomember,
        name="addunknowntagtomember",
    ),
    path(
        "addmembertounknowntag/<int:user_id>",
        views.addmembertounknowntag,
        name="addmembertounknowntag",
    ),
    # Temporary hack to work around https://github.com/openssl/openssl/issues/6933
    # in master.py until we've either upgrade, retired this code; or simplified
    # our URL routing further.
    path("api-int/v1/unknowntag", views.unknowntag, name="unknowntag-int"),
]
