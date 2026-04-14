from rest_framework import permissions, serializers, viewsets

from .models import Session


class SessionSerializer(serializers.ModelSerializer):
    customer_full_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)

    class Meta:
        model = Session
        fields = [
            "id",
            "session_id",
            "username",
            "mac_address",
            "ip_address",
            "status",
            "started_at",
            "ended_at",
            "input_octets",
            "output_octets",
            "total_octets",
            "duration_seconds",
            "customer_full_name",
            "customer_phone",
        ]


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Session.objects.select_related("customer", "entitlement", "nas").all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["status", "username", "customer__phone"]
    search_fields = ["session_id", "username", "mac_address", "customer__full_name", "customer__phone"]
