from django.db.models import Sum
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from audit.models import AuditLog
from payments.models import Payment
from sessions.models import Session, SessionStatus


@staff_member_required
def index(request):
    context = {
        "active_sessions": Session.objects.filter(status=SessionStatus.ACTIVE).count(),
        "active_customers": Session.objects.filter(status=SessionStatus.ACTIVE)
        .values("username")
        .distinct()
        .count(),
        "revenue_total": Payment.objects.filter(status="success").aggregate(total=Sum("amount"))["total"] or 0,
    }
    return render(request, "dashboard/index.html", context)


@staff_member_required
def active_sessions(request):
    rows = (
        Session.objects.select_related("customer")
        .filter(status=SessionStatus.ACTIVE)
        .order_by("-started_at")[:100]
    )
    return render(request, "dashboard/active_sessions.html", {"sessions": rows})


@staff_member_required
def auth_issues(request):
    rows = AuditLog.objects.filter(action="portal_login_failed").order_by("-created_at")[:100]
    return render(request, "dashboard/auth_issues.html", {"rows": rows})
