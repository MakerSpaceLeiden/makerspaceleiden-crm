import logging

from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware, utc
from rest_framework import response, viewsets

from acl.models import Machine
from agenda.models import Agenda
from members.models import User

from .serializers import AgendaSerializer, MachineSerializer, UserSerializer

logger = logging.getLogger(__name__)


# ViewSets define the view behavior.
class BaseListMetaViewSet(viewsets.ModelViewSet):
    """
    A base viewset that wraps list responses in a consistent meta/data structure.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            page if page is not None else queryset, many=True
        )
        resp = {
            "meta": {
                "total": queryset.count(),
            },
            "data": serializer.data,
        }
        if page is not None:
            return self.get_paginated_response(
                {
                    "meta": {
                        "total": queryset.count(),
                    },
                    "data": serializer.data,
                }
            )
        return response.Response(resp)


class UserViewSet(BaseListMetaViewSet):
    queryset = User.objects.all().filter(is_active=True)
    serializer_class = UserSerializer


class EventViewSet(BaseListMetaViewSet):
    queryset = Agenda.objects.all().order_by("startdatetime")
    serializer_class = AgendaSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        start_datetime_str = request.query_params.get("start_datetime")
        end_datetime_str = request.query_params.get("end_datetime")

        if start_datetime_str:
            queryset = self._filter_by_datetime_field(
                queryset, "startdatetime", start_datetime_str, "gte"
            )
        if end_datetime_str:
            queryset = self._filter_by_datetime_field(
                queryset, "enddatetime", end_datetime_str, "lte"
            )

        self.get_queryset = lambda: queryset
        return super().list(request, *args, **kwargs)

    def _filter_by_datetime_field(self, queryset, field: str, dt_str: str, lookup: str):
        dt = parse_datetime(dt_str)
        if dt is None:
            logger.warning("Invalid datetime string provided", dt_str)
            return queryset
        if is_naive(dt):
            dt = make_aware(dt, utc)
        # Use Django's ORM filtering for the datetime field
        filter_expr = {f"{field}__{lookup}": dt}
        return queryset.filter(**filter_expr)


class MachineViewSet(BaseListMetaViewSet):
    queryset = Machine.objects.all().filter(do_not_show=False)
    serializer_class = MachineSerializer

    ALLOWED_FILTER_FIELDS = {"out_of_order", "category", "location", "name", "id"}

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        filter_kwargs = {}
        for field in self.ALLOWED_FILTER_FIELDS:
            value = request.query_params.get(field, None)
            if value is not None:
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                filter_kwargs[field] = value
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        # Use the parent's list logic for pagination and response
        self.get_queryset = lambda: queryset
        return super().list(request, *args, **kwargs)
