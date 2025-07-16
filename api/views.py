from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_naive, make_aware, utc
from rest_framework import response, viewsets

from acl.models import Machine
from agenda.models import Agenda
from members.models import User

from .serializers import AgendaSerializer, MachineSerializer, UserSerializer


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
    queryset = Agenda.objects.all()
    serializer_class = AgendaSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        start_datetime_str = request.query_params.get("start_datetime")
        end_datetime_str = request.query_params.get("end_datetime")

        if start_datetime_str:
            queryset = filter_by_datetime(queryset, "start", start_datetime_str, ">=")
        if end_datetime_str:
            queryset = filter_by_datetime(queryset, "end", end_datetime_str, "<=")
        self.get_queryset = lambda: queryset
        return super().list(request, *args, **kwargs)


def filter_by_datetime(queryset, prefix, dt_str, op):
    dt = parse_datetime(dt_str)
    if dt and is_naive(dt):
        dt = make_aware(dt, utc)
    if dt:
        date_field = f"{prefix}date__isnull"
        time_field = f"{prefix}time__isnull"
        where = f"({prefix}date || ' ' || {prefix}time) {op} %s"
        queryset = queryset.filter(**{date_field: False, time_field: False}).extra(
            where=[where],
            params=[dt.strftime("%Y-%m-%d %H:%M:%S")],
        )
    return queryset


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
