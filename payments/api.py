from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from plans.models import Plan

from .services import PaymentProviderError, initialize_plan_purchase, verify_plan_purchase


class PurchaseInitializeSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    full_name = serializers.CharField(max_length=160)
    mobile = serializers.CharField(max_length=32)


class PurchaseVerifySerializer(serializers.Serializer):
    reference = serializers.CharField(max_length=128)


class PurchaseInitializeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PurchaseInitializeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        plan = Plan.objects.filter(id=payload["plan_id"], is_active=True).first()
        if not plan:
            return Response({"detail": "Plan not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            purchase = initialize_plan_purchase(
                plan=plan,
                full_name=payload["full_name"],
                mobile=payload["mobile"],
            )
        except PaymentProviderError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "payment_id": str(purchase.payment.id),
                "reference": purchase.reference,
                "authorization_url": purchase.authorization_url,
                "access_code": purchase.access_code,
                "customer_id": str(purchase.customer.id),
                "customer_mobile": purchase.customer.phone,
            },
            status=status.HTTP_201_CREATED,
        )


class PurchaseVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PurchaseVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._verify(serializer.validated_data["reference"])

    def get(self, request):
        reference = request.query_params.get("reference", "").strip()
        if not reference:
            return Response({"detail": "Reference is required."}, status=status.HTTP_400_BAD_REQUEST)
        return self._verify(reference)

    def _verify(self, reference: str):
        try:
            result = verify_plan_purchase(reference)
        except PaymentProviderError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "payment_id": str(result.payment.id),
                "status": result.payment.status,
                "reference": result.payment.provider_reference,
                "voucher_code": result.voucher.code if result.voucher else None,
                "sms_sent": result.sms_sent,
                "sms_error": result.sms_error,
                "login_identity": result.customer.phone or result.customer.username,
            },
            status=status.HTTP_200_OK,
        )
