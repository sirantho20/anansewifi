import secrets

from django.conf import settings
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from sessions.services import ingest_accounting_event


class RadiusAccountingSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=["start", "interim", "stop"])
    username = serializers.CharField()
    session_id = serializers.CharField()
    framed_ip_address = serializers.IPAddressField(required=False)
    calling_station_id = serializers.CharField(required=False, allow_blank=True)
    nas_ip_address = serializers.IPAddressField(required=False)
    input_octets = serializers.IntegerField(required=False, default=0)
    output_octets = serializers.IntegerField(required=False, default=0)
    duration_seconds = serializers.IntegerField(required=False, default=0)
    terminate_cause = serializers.CharField(required=False, allow_blank=True)


class RadiusAccountingIngestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if settings.RADIUS_ACCOUNTING_INGEST_TOKEN:
            provided_token = request.headers.get("X-Radius-Token", "")
            if not secrets.compare_digest(provided_token, settings.RADIUS_ACCOUNTING_INGEST_TOKEN):
                return Response({"detail": "Unauthorized."}, status=401)

        serializer = RadiusAccountingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = ingest_accounting_event(serializer.validated_data)
        return Response({"record_id": str(record.id), "status": "ingested"})
