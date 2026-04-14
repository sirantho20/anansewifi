from rest_framework import permissions
from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from payments.models import Payment
from sessions.models import AccountingRecord, Session, SessionStatus


class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        active_sessions = Session.objects.filter(status=SessionStatus.ACTIVE).count()
        data_usage = AccountingRecord.objects.aggregate(
            total_input=Sum("input_octets"),
            total_output=Sum("output_octets"),
        )
        revenue = (
            Payment.objects.filter(status="success")
            .aggregate(total=Sum("amount"))
            .get("total")
            or 0
        )
        return Response(
            {
                "active_sessions": active_sessions,
                "total_input_octets": data_usage["total_input"] or 0,
                "total_output_octets": data_usage["total_output"] or 0,
                "revenue_total": revenue,
            }
        )
