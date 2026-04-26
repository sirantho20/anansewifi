import pytest
from types import SimpleNamespace
from unittest.mock import patch

from payments.models import Payment
from plans.models import Plan

from .factories import CustomerFactory, VoucherFactory


@pytest.mark.django_db
def test_portal_login_get_shows_wi_fi_page_and_plans_link(client):
    response = client.get("/portal/login/")
    assert response.status_code == 200
    assert b'data-testid="portal-wifi-login"' in response.content
    assert b"/portal/plans/" in response.content
    assert b"Ananse WiFi" in response.content
    assert b"Connect to" in response.content and b"Wi" in response.content


@pytest.mark.django_db
def test_portal_login_redeems_voucher(client):
    customer = CustomerFactory(username="portaluser", phone="+233241234567")
    voucher = VoucherFactory()

    response = client.post(
        "/portal/login/",
        {"identity": customer.phone, "voucher_code": voucher.code, "mac_address": "AA:BB:CC:00:00:01"},
        follow=True,
    )

    assert response.status_code == 200
    assert b"Session Status" in response.content


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
