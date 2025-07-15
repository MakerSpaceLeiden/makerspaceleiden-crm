from rest_framework import response, serializers, viewsets

from acl.models import Location, Machine
from members.models import User
from servicelog.models import Servicelog


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["id", "url", "email", "first_name", "last_name", "image"]


class ServicelogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicelog
        fields = ["last_updated", "description"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name"]


class MachineSerializer(serializers.HyperlinkedModelSerializer):
    logs = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        model = Machine
        fields = [
            "id",
            "name",
            "out_of_order",
            "description",
            "category",
            "location",
            "last_updated",
            "logs",
        ]

    def get_logs(self, obj):
        # This will return a list of description strings for each related servicelog
        return [log.description for log in obj.servicelog_set.all()]

    def get_last_updated(self, obj):
        # Get the most recent last_updated from related servicelogs
        latest_log = obj.servicelog_set.order_by("-last_updated").first()
        return latest_log.last_updated if latest_log else None

    def get_location(self, obj):
        return obj.location.name if obj.location else None


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().filter(is_active=True)
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Wrap paginated response
            return self.get_paginated_response({"data": serializer.data})

        serializer = self.get_serializer(queryset, many=True)
        return response.Response(
            {
                "meta": {
                    "count": queryset.count(),
                },
                "data": serializer.data,
            }
        )


class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all().filter(do_not_show=False)
    serializer_class = MachineSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Wrap paginated response
            return self.get_paginated_response({"data": serializer.data})

        serializer = self.get_serializer(queryset, many=True)
        return response.Response(
            {
                "meta": {
                    "count": queryset.count(),
                },
                "data": serializer.data,
            }
        )
