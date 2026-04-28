import pytest
from types import SimpleNamespace
from unittest.mock import patch

from payments.models import Payment, PaymentStatus
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
    assert b"data-portal-login-reveal" in response.content
    assert b'id="portal-login-forms"' in response.content
    assert b'class="space-y-8 hidden"' in response.content


@pytest.mark.django_db
def test_portal_login_redeems_voucher(client):
    customer = CustomerFactory(username="portaluser", phone="+233241234567")
    voucher = VoucherFactory()
    Payment.objects.create(
        customer=customer,
        plan=voucher.plan,
        voucher=voucher,
        amount=voucher.plan.price,
        status=PaymentStatus.SUCCESS,
        provider="test",
    )

    response = client.post(
        "/portal/login/",
        {
            "auth_mode": "voucher",
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
    assert voucher.code.encode() in response.content
    assert b"Login with Voucher" in response.content
    assert b'name="auth_mode"' in response.content
    assert b'value="voucher"' in response.content
    assert b'name="voucher_code"' in response.content
    mock_verify_purchase.assert_called_once_with("ANW-TRXREF-001")


@pytest.mark.django_db
def test_portal_purchase_start_invalid_mobile_shows_validation_error(client):
    plan = Plan.objects.create(
        name="Buy Invalid Mobile Plan",
        price="5.00",
        billing_type="voucher",
        quota_type="duration",
        duration_minutes=60,
        is_active=True,
    )
    response = client.post(
        "/portal/purchase/start/",
        {
            "plan_id": str(plan.id),
            "full_name": "Test User",
            "mobile": "not-a-ghana-number",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert b"Invalid mobile number format" in response.content


@pytest.mark.django_db
@patch("portal.views.initialize_plan_purchase")
def test_portal_purchase_start_redirects_to_paystack_checkout(mock_initialize_plan_purchase, client):
    customer = CustomerFactory(phone="+233241234588")
    plan = Plan.objects.create(
        name="Checkout Redirect Plan",
        price="5.00",
        billing_type="voucher",
        quota_type="duration",
        duration_minutes=60,
        is_active=True,
    )
    mock_initialize_plan_purchase.return_value = SimpleNamespace(
        customer=customer,
        payment=SimpleNamespace(id=1001),
        authorization_url="https://checkout.paystack.com/mock-verify-path",
        access_code="mock_access_code",
        reference="mock-ref-portal-flow",
    )

    response = client.post(
        "/portal/purchase/start/",
        {
            "plan_id": str(plan.id),
            "full_name": "Paid Customer",
            "mobile": "0241555888",
        },
        follow=False,
        HTTP_HOST="127.0.0.1:18080",
    )

    assert response.status_code == 302
    assert response["Location"] == "https://checkout.paystack.com/mock-verify-path"
    mock_initialize_plan_purchase.assert_called_once()
    kwargs = mock_initialize_plan_purchase.call_args.kwargs
    cu = kwargs.get("callback_url", "")
    assert cu.startswith("http://127.0.0.1:18080"), (
        "Paystack redirect must hit the bound host:port so browsers do not GET port 80. "
        f"Got callback_url={cu!r}"
    )
    assert "/portal/purchase/callback/" in cu
