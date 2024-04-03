from django.urls import path

from . import views

urlpatterns = [
    path("me", views.member_overview, name="my_page"),
    path("acl/personal_page", views.member_overview, name="personal_page"),
    path("acl/member/<int:member_id>", views.member_overview, name="overview"),
    path("acl/member/", views.members, name="overview"),
    path("acl/tag/edit/<int:tag_id>", views.tag_edit, name="tag_edit"),
    path("acl/tag/delete/<int:tag_id>", views.tag_delete, name="tag_delete"),
    path(
        "acl/machine/<int:machine_id>", views.machine_overview, name="machine_overview"
    ),
    path("acl/machine/", views.machine_overview, name="machine_overview"),
    path("acl/machines", views.machine_list, name="machine_list"),
    # For the trusteeds - to ease admin.
    path("acl/missing_forms/", views.missing_forms, name="missing_forms"),
    path("acl/filed_forms/", views.filed_forms, name="filed_forms"),
    # Convenience page to debug the API
    path("acl/", views.api_index, name="acl-index"),
    # API oriented
    path("acl/api/v1/getok/<str:machine>", views.api_getok, name="acl-v1-getok"),
    path(
        "acl/api/v1/getok4node/<str:node>",
        views.api_getok_by_node,
        name="acl-v1-getok4-node",
    ),
    path("acl/api/v1/gettaginfo", views.api_gettaginfo, name="acl-v1-gettaginfo"),
    path("acl/<int:machine_id>", views.api_details, name="details"),
]
