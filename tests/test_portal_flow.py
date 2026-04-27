import pytest
from types import SimpleNamespace
from unittest.mock import patch

from payments.models import Payment
from plans.models import Plan, SpeedProfile
from radius_integration.services import sync_entitlement_to_radius
from sessions.models import Entitlement

from .factories import CustomerFactory, VoucherFactory


@pytest.mark.django_db
def test_portal_login_get_shows_wi_fi_page_and_plans_link(client):
    response = client.get("/portal/login/")
    assert response.status_code == 200
    assert b'data-testid="portal-wifi-login"' in response.content
    assert b"/portal/packages/" in response.content
    assert b"Ananse WiFi" in response.content
    assert b"Connect to" in response.content and b"Wi" in response.content
    assert b"MAC address" not in response.content
    assert b"Redeem a voucher" in response.content
    assert b"Sign in with username" in response.content


@pytest.mark.django_db
def test_portal_login_redeems_voucher(client):
    customer = CustomerFactory(username="portaluser", phone="+233241234567")
    voucher = VoucherFactory()

    response = client.post(
        "/portal/login/",
        {
            "auth_mode": "voucher",
            "identity": customer.phone,
            "voucher_code": voucher.code,
        },
        follow=True,
    )

    assert response.status_code == 200
    assert b"Session Status" in response.content


@pytest.mark.django_db
def test_portal_password_login_succeeds(client):
    sp = SpeedProfile.objects.create(
        name="pw-login-speed",
        up_rate_kbps=1024,
        down_rate_kbps=2048,
        mikrotik_rate_limit="1M/2M",
    )
    plan = Plan.objects.create(
        name="pw-login-plan",
        price=5,
        duration_minutes=60,
        speed_profile=sp,
        idle_timeout_seconds=300,
        session_timeout_seconds=1800,
    )
    customer = CustomerFactory(username="pw-portal-user", phone="+233241234500")
    entitlement = Entitlement.objects.create(customer=customer, plan=plan, status="active")
    sync_entitlement_to_radius(
        username=customer.username,
        cleartext_password="wifi-secret-xyz",
        entitlement=entitlement,
    )

    response = client.post(
        "/portal/login/",
        {
            "auth_mode": "password",
            "identity": customer.phone,
            "wifi_password": "wifi-secret-xyz",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert b"Session Status" in response.content


@pytest.mark.django_db
def test_portal_password_login_rejects_wrong_password(client):
    sp = SpeedProfile.objects.create(
        name="pw-bad-speed",
        up_rate_kbps=1024,
        down_rate_kbps=2048,
        mikrotik_rate_limit="1M/2M",
    )
    plan = Plan.objects.create(
        name="pw-bad-plan",
        price=5,
        duration_minutes=60,
        speed_profile=sp,
        idle_timeout_seconds=300,
        session_timeout_seconds=1800,
    )
    customer = CustomerFactory(username="pw-bad-user", phone="+233241234501")
    entitlement = Entitlement.objects.create(customer=customer, plan=plan, status="active")
    sync_entitlement_to_radius(
        username=customer.username,
        cleartext_password="correct-pass",
        entitlement=entitlement,
    )

    response = client.post(
        "/portal/login/",
        {
            "auth_mode": "password",
            "identity": customer.phone,
            "wifi_password": "wrong-pass",
        },
    )

    assert response.status_code == 200
    assert b"Login failed" in response.content
    assert b"Session Status" not in response.content


@pytest.mark.django_db
@patch("portal.views.verify_plan_purchase")
def test_purchase_callback_accepts_trxref_query_param(mock_verify_purchase, client):
    customer = CustomerFactory(username="buyer-portal", phone="+233241234567")
    plan = Plan.objects.create(
        name="Portal Plan",
        price="5.00",
        billing_type="voucher",
        quota_type="duration",
        duration_minutes=60,
    )
    payment = Payment.objects.create(
        customer=customer,
        plan=plan,
        amount=plan.price,
        provider="paystack",
        provider_reference="ANW-TRXREF-001",
    )
    voucher = VoucherFactory(plan=plan)
    mock_verify_purchase.return_value = SimpleNamespace(
        customer=customer,
        payment=payment,
        voucher=voucher,
        sms_sent=True,
        sms_error="",
    )

    response = client.get("/portal/purchase/callback/?trxref=ANW-TRXREF-001")

    assert response.status_code == 200
    assert b"Purchase successful" in response.content
    mock_verify_purchase.assert_called_once_with("ANW-TRXREF-001")
