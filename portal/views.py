from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.urls import reverse

from audit.models import AuditLog
from customers.services import find_customer_by_identity
from plans.models import Plan
from payments.services import (
    PaymentProviderError,
    find_customer_for_voucher_purchase,
    initialize_plan_purchase,
    verify_plan_purchase,
)
from radius_integration.services import verify_radius_cleartext_password
from sessions.models import Entitlement
from vouchers.services import redeem_voucher


def _portal_site_title() -> str:
    return settings.DAISY_SETTINGS.get("SITE_TITLE", "Ananse WiFi")


def plans_view(request):
    plans = (
        Plan.objects.filter(is_active=True)
        .select_related("speed_profile")
        .order_by("-is_featured", "price", "name")
    )
    site_title = _portal_site_title()
    return render(
        request,
        "portal/plans.html",
        {
            "plans": plans,
            "payment_currency": settings.PAYMENT_CURRENCY,
            "site_title": site_title,
        },
    )


def login_view(request):
    if request.method == "POST":
        auth_mode = request.POST.get("auth_mode", "voucher")
        identity = request.POST.get("identity", "").strip()
        if auth_mode == "password":
            wifi_password = request.POST.get("wifi_password", "")
            try:
                customer = find_customer_by_identity(identity)
                if not customer:
                    raise ValueError("Customer not found for the provided username/mobile.")
                if not verify_radius_cleartext_password(
                    customer=customer,
                    cleartext_password=wifi_password,
                ):
                    raise ValueError("Invalid username/mobile or password.")
                AuditLog.objects.create(
                    actor=customer.phone or customer.username,
                    action="portal_password_login",
                    target_type="Customer",
                    target_id=customer.username,
                    details={},
                )
                messages.success(request, "Signed in successfully.")
                return redirect("portal:session-status", username=customer.username)
            except Exception as exc:  # noqa: BLE001
                AuditLog.objects.create(
                    actor=identity or "anonymous",
                    action="portal_login_failed",
                    target_type="Customer",
                    target_id=identity or "unknown",
                    details={"error": str(exc), "auth_mode": "password"},
                )
                messages.error(request, f"Login failed: {exc}")
        else:
            voucher_code = request.POST.get("voucher_code", "")
            try:
                customer = find_customer_for_voucher_purchase(voucher_code)
                if not customer:
                    raise ValueError(
                        "We couldn't match this voucher to a purchase. If you bought a package, "
                        "enter the exact code from SMS, or contact support."
                    )
                redeem_voucher(voucher_code, customer, mac_address="")
                AuditLog.objects.create(
                    actor=customer.phone or customer.username,
                    action="voucher_redeemed",
                    target_type="Voucher",
                    target_id=voucher_code,
                    details={},
                )
                messages.success(request, "Voucher redeemed successfully.")
                return redirect("portal:session-status", username=customer.username)
            except Exception as exc:  # noqa: BLE001
                AuditLog.objects.create(
                    actor=identity or "anonymous",
                    action="portal_login_failed",
                    target_type="Voucher",
                    target_id=voucher_code or "unknown",
                    details={"error": str(exc), "auth_mode": "voucher"},
                )
                messages.error(request, f"Login failed: {exc}")
    return render(
        request,
        "portal/login.html",
        {
            "identity": request.GET.get("identity", ""),
            "site_title": _portal_site_title(),
            "reveal_login_forms": request.method == "POST",
        },
    )


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
        {
            "username": username,
            "entitlement": active_entitlement,
            "customer": customer,
            "site_title": _portal_site_title(),
        },
    )


def purchase_start_view(request):
    if request.method != "POST":
        return redirect("portal:packages")

    plan_id = request.POST.get("plan_id", "")
    full_name = request.POST.get("full_name", "").strip()
    mobile = request.POST.get("mobile", "").strip()
    if not full_name or not mobile:
        messages.error(request, "Please enter your full name and mobile number.")
        return redirect("portal:packages")
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
    except ValueError as exc:
        messages.error(request, str(exc))
        AuditLog.objects.create(
            actor=mobile or "anonymous",
            action="purchase_initialize_failed",
            target_type="Plan",
            target_id=plan_id or "unknown",
            details={"error": str(exc), "full_name": full_name, "kind": "validation"},
        )
        return redirect("portal:packages")
    except Exception as exc:  # noqa: BLE001
        messages.error(request, f"Could not start payment: {exc}")
        AuditLog.objects.create(
            actor=mobile or "anonymous",
            action="purchase_initialize_failed",
            target_type="Plan",
            target_id=plan_id or "unknown",
            details={"error": str(exc), "full_name": full_name},
        )
        return redirect("portal:packages")


def purchase_callback_view(request):
    reference = (request.GET.get("reference") or request.GET.get("trxref") or "").strip()
    if not reference:
        messages.error(request, "Missing payment reference.")
        return redirect("portal:packages")

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
        return redirect("portal:packages")

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
            "site_title": _portal_site_title(),
            "purchase_success_nav": True,
        },
    )
