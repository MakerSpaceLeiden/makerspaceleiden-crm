from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="chores"),
    path("api/v1/list/<str:name>", views.index_api, name="chores_api"),
    path("api/v1/list", views.index_api, name="chores_api"),
    path("signup/<int:chore_id>/<int:ts>", views.signup, name="signup_chore"),
    path(
        "remove/<int:chore_id>/<int:ts>",
        views.remove_signup,
        name="remove_signup_chore",
    ),
]
