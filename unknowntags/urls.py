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
    # Terminal checking version of unknown tag registration; unlike above
    # api/v1/unknowntag it will only return an ok/nok - not return a list
    # when called without a tag.
    path("api/v2/unknowntag", views.reg_unknowntag, name="unknowntag-v2"),
]
