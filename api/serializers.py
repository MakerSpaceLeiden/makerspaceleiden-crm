from rest_framework import serializers

from acl.models import Location, Machine
from agenda.models import Agenda
from makerspaceleiden.utils import generate_signed_url
from members.models import User
from servicelog.models import Servicelog


# Serializers define the API representation.
class AgendaSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    start_datetime = serializers.SerializerMethodField()
    end_datetime = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Agenda
        fields = [
            "id",
            "name",
            "description",
            "start_datetime",
            "end_datetime",
            "type",
            "status",
        ]

    def get_name(self, obj):
        return obj.item_title

    def get_description(self, obj):
        return obj.item_details

    def get_status(self, obj):
        return None if obj.display_status == "" else obj.display_status

    def get_start_datetime(self, obj):
        dt = obj.start_datetime
        if dt:
            from django.utils import timezone

            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            return dt.isoformat().replace("+00:00", "Z")
        return None

    def get_end_datetime(self, obj):
        dt = obj.end_datetime
        if dt:
            from django.utils import timezone

            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            return dt.isoformat().replace("+00:00", "Z")
        return None


def generate_absolute_signed_uri(request, full_image_path):
    last_chunk = full_image_path.split("/")[-1]
    signed_chunk = generate_signed_url(last_chunk)
    return request.build_absolute_uri(full_image_path.replace(last_chunk, signed_chunk))


class UserSerializer(serializers.HyperlinkedModelSerializer):
    image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "url",
            "email",
            "first_name",
            "last_name",
            "image",
            "images",
            "is_onsite",
        ]

    def get_image(self, obj):
        return generate_absolute_signed_uri(
            self.context["request"], obj.image_url("thumbnail")
        )

    def get_images(self, obj):
        return {
            "original": generate_absolute_signed_uri(
                self.context["request"], obj.image_url("original")
            ),
            "thumbnail": generate_absolute_signed_uri(
                self.context["request"],
                obj.image_url("thumbnail"),
            ),
        }


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
        return [
            {
                "description": log.description,
                "reported": log.reported,
                "last_updated": log.last_updated,
            }
            for log in obj.servicelog_set.all()
        ]

    def get_last_updated(self, obj):
        # Get the most recent last_updated from related servicelogs
        latest_log = obj.servicelog_set.order_by("-last_updated").first()
        return latest_log.last_updated if latest_log else None

    def get_location(self, obj):
        return obj.location.name if obj.location else None
