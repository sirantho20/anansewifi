from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.urls import reverse

from audit.models import AuditLog
from customers.services import find_customer_by_identity
from plans.models import Plan
from payments.services import (
    PaymentProviderError,
    initialize_plan_purchase,
    verify_plan_purchase,
)
from sessions.models import Entitlement
from vouchers.services import redeem_voucher


def plans_view(request):
    return render(request, "portal/plans.html", {"plans": Plan.objects.filter(is_active=True)})


def login_view(request):
    if request.method == "POST":
        identity = request.POST.get("identity", "").strip()
        voucher_code = request.POST.get("voucher_code", "")
        mac_address = request.POST.get("mac_address", "")
        try:
            customer = find_customer_by_identity(identity)
            if not customer:
                raise ValueError("Customer not found for the provided username/mobile.")
            redeem_voucher(voucher_code, customer, mac_address=mac_address)
            AuditLog.objects.create(
                actor=customer.phone or customer.username,
                action="voucher_redeemed",
                target_type="Voucher",
                target_id=voucher_code,
                details={"mac_address": mac_address},
            )
            messages.success(request, "Voucher redeemed successfully.")
            return redirect("portal:session-status", username=customer.username)
        except Exception as exc:  # noqa: BLE001
            AuditLog.objects.create(
                actor=identity or "anonymous",
                action="portal_login_failed",
                target_type="Voucher",
                target_id=voucher_code or "unknown",
                details={"error": str(exc), "mac_address": mac_address},
            )
            messages.error(request, f"Login failed: {exc}")
    return render(request, "portal/login.html", {"identity": request.GET.get("identity", "")})


def session_status_view(request, username: str):
    active_entitlement = (
        Entitlement.objects.select_related("plan", "customer")
        .filter(customer__username=username, status="active")
        .first()
    )
    customer = active_entitlement.customer if active_entitlement and active_entitlement.customer else None
    return render(
        request,
        "portal/session_status.html",
        {"username": username, "entitlement": active_entitlement, "customer": customer},
    )


def purchase_start_view(request):
    if request.method != "POST":
        return redirect("portal:plans")

    plan_id = request.POST.get("plan_id", "")
    full_name = request.POST.get("full_name", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    try:
        callback_url = request.build_absolute_uri(reverse("portal:purchase-callback"))
        purchase = initialize_plan_purchase(
            plan=plan,
            full_name=full_name,
            mobile=mobile,
            callback_url=callback_url,
        )
        AuditLog.objects.create(
            actor=purchase.customer.phone or purchase.customer.username,
            action="purchase_initialized",
            target_type="Payment",
            target_id=str(purchase.payment.id),
            details={
                "plan_id": str(plan.id),
                "reference": purchase.reference,
            },
        )
        return redirect(purchase.authorization_url)
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f"Could not start payment: {exc}")
        AuditLog.objects.create(
            actor=mobile or "anonymous",
            action="purchase_initialize_failed",
            target_type="Plan",
            target_id=plan_id or "unknown",
            details={"error": str(exc), "full_name": full_name},
        )
        return redirect("portal:plans")


def purchase_callback_view(request):
    reference = (request.GET.get("reference") or request.GET.get("trxref") or "").strip()
    if not reference:
        messages.error(request, "Missing payment reference.")
        return redirect("portal:plans")

    try:
        result = verify_plan_purchase(reference)
    except PaymentProviderError as exc:
        messages.error(request, f"Payment verification failed: {exc}")
        AuditLog.objects.create(
            actor=reference,
            action="purchase_verify_failed",
            target_type="Payment",
            target_id=reference,
            details={"error": str(exc)},
        )
        return redirect("portal:plans")

    AuditLog.objects.create(
        actor=result.customer.phone or result.customer.username,
        action="purchase_verified",
        target_type="Payment",
        target_id=str(result.payment.id),
        details={
            "reference": reference,
            "voucher_code": result.voucher.code if result.voucher else "",
            "sms_sent": result.sms_sent,
            "sms_error": result.sms_error,
        },
    )
    return render(
        request,
        "portal/purchase_result.html",
        {
            "customer": result.customer,
            "payment": result.payment,
            "voucher": result.voucher,
            "sms_sent": result.sms_sent,
            "sms_error": result.sms_error,
            "login_identity": result.customer.phone or result.customer.username,
        },
    )
