from rest_framework import serializers, viewsets

from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "code",
            "description",
            "price",
            "billing_type",
            "quota_type",
            "duration_minutes",
            "data_bytes",
            "concurrent_device_limit",
            "idle_timeout_seconds",
            "session_timeout_seconds",
            "is_active",
        ]


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True).select_related("speed_profile")
    serializer_class = PlanSerializer
    filterset_fields = ["billing_type", "quota_type"]
    search_fields = ["name", "code"]
