from django.urls import path

from . import views

urlpatterns = [
    path("me", views.member_overview, name="my_page"),
    path("acl/personal_page", views.member_overview, name="personal_page"),
    path("acl/member/<int:member_id>", views.member_overview, name="overview"),
    path(
        "acl/member/delete/<int:member_id>",
        views.member_delete_confirm,
        name="userdelete",
    ),
    path(
        "acl/member/delete_confirm/<int:member_id>",
        views.member_delete,
        name="userdelete_confirm",
    ),
    path("acl/member/", views.members_list, name="overview"),
    path("acl/tag/edit/<int:tag_id>", views.tag_edit, name="tag_edit"),
    path("acl/tag/delete/<int:tag_id>", views.tag_delete, name="tag_delete"),
    path(
        "acl/machine/<int:machine_id>", views.machine_overview, name="machine_overview"
    ),
    path("acl/machine/", views.machine_overview, name="machine_overview"),
    path("acl/machines", views.machine_list, name="machine_list"),
    # For the trustees - to ease admin.
    path("acl/missing_forms/", views.missing_forms, name="missing_forms"),
    path("acl/missing_doors/", views.missing_doors, name="missing_doors"),
    path("acl/filed_forms/", views.filed_forms, name="filed_forms"),
    # Convenience page to debug the API
    path("acl/", views.api_index, name="acl-index"),
    # API calls
    #
    # calls to give an ok/nok for a machine or node given a tag. Requires
    # a bearer token or superuser credentials along with a valid tag.
    #
    path("acl/api/v1/getok/<str:machine>", views.api_getok, name="acl-v1-getok"),
    path(
        "acl/api/v1/getok4node/<str:node>",
        views.api_getok_by_node,
        name="acl-v1-getok4-node",
    ),
    # Hack - this bypasses the optional_CA to work around this
    # https://github.com/openssl/openssl/issues/6933 bug in python
    # until the moment we've retired this master agent.
    path(
        "acl/api-int/v1/getok/<str:machine>",
        views.api_getok,
        name="acl-v1-getok-internal",
    ),
    # Provide metadata on a tag, requires a valid tag and a bearer token.
    #
    # Provide metadata on a machine - propably no longer used. Requires
    # a bearer token.
    #
    path("acl/<int:machine_id>", views.api_details, name="details"),
    path(
        "acl/api/v1/getchangecounter",
        views.api_getchangecounter,
        name="acl-v1-getchangecounter",
    ),
    path(
        "acl/api/v1/getchangecounterJSON",
        views.api_getchangecounterJSON,
        name="acl-v1-getchangecounterJSON",
    ),
    path(
        "acl/api/v1/gettags4machineBIN/<str:machine>",
        views.api_gettags4machineBIN,
        name="acl-v1-gettags-bin",
    ),
    path(
        "acl/api/v2/gettags4machineBIN/<str:machine>",
        views.api2_gettags4machineBIN,
        name="acl-v2-gettags-bin",
    ),
    path(
        "acl/api/v2/recorduse/<str:machine>",
        views.api_recorduse,
        name="acl-v2-recorduse",
    ),
]
