from rest_framework import serializers, viewsets

from .models import NASDevice


class NASDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NASDevice
        fields = ["id", "name", "ip_address", "shortname", "description", "is_active", "site"]


class NASDeviceViewSet(viewsets.ModelViewSet):
    queryset = NASDevice.objects.select_related("site").all()
    serializer_class = NASDeviceSerializer
    filterset_fields = ["site", "is_active"]
    search_fields = ["name", "ip_address", "shortname"]
