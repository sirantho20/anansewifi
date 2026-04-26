from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from customers.services import find_customer_by_identity

from .models import Voucher
from .services import redeem_voucher


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ["id", "code", "status", "plan", "expires_at", "redeemed_at", "max_uses", "use_count"]


class VoucherRedeemSerializer(serializers.Serializer):
    code = serializers.CharField()
    identity = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    mobile = serializers.CharField(required=False, allow_blank=True)
    mac_address = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not (attrs.get("identity") or attrs.get("username") or attrs.get("mobile")):
            raise serializers.ValidationError("Provide identity, username, or mobile.")
        return attrs


class VoucherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Voucher.objects.select_related("plan", "redeemed_by").all()
    serializer_class = VoucherSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["status", "plan"]
    search_fields = ["code", "redeemed_by__username"]

    def get_permissions(self):
        if self.action == "redeem":
            return [permissions.AllowAny()]
        return [permission() for permission in self.permission_classes]

    @action(detail=False, methods=["post"], url_path="redeem")
    def redeem(self, request):
        serializer = VoucherRedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        identity = (
            payload.get("identity")
            or payload.get("mobile")
            or payload.get("username")
            or ""
        )
        customer = find_customer_by_identity(identity)
        if not customer:
            return Response({"detail": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            result = redeem_voucher(
                code=payload["code"],
                customer=customer,
                mac_address=payload.get("mac_address", ""),
            )
        except Voucher.DoesNotExist:
            return Response({"detail": "Voucher not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "voucher": VoucherSerializer(result.voucher).data,
                "entitlement_id": str(result.entitlement.id),
            },
            status=status.HTTP_200_OK,
        )
