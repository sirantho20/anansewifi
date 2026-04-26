from rest_framework import permissions, serializers, viewsets

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "username", "full_name", "phone", "email", "is_active", "last_seen_at"]


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["is_active"]
    search_fields = ["username", "full_name", "phone", "email"]
