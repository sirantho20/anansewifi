import pytest
from unittest.mock import patch
from rest_framework.test import APIClient

from plans.models import Plan
from payments.models import Payment, PaymentStatus
from .factories import CustomerFactory, PlanFactory, VoucherFactory


@pytest.mark.django_db
def test_plans_api_returns_data():
    before = Plan.objects.count()
    PlanFactory()
    client = APIClient()
    response = client.get("/api/plans/")
    assert response.status_code == 200
    assert response.data["count"] == before + 1


@pytest.mark.django_db
def test_voucher_redeem_api():
    customer = CustomerFactory(username="redeemer")
    voucher = VoucherFactory()
    client = APIClient()
    response = client.post(
        "/api/vouchers/redeem/",
        {"code": voucher.code, "username": customer.username, "mac_address": "AA:BB:CC:DD:EE:00"},
        format="json",
    )
    assert response.status_code == 200
    assert "entitlement_id" in response.data


@pytest.mark.django_db
@patch("payments.services.PaystackClient.initialize_transaction")
def test_purchase_initialize_api_returns_checkout_url(mock_initialize):
    plan = PlanFactory(price=12)
    client = APIClient()
    mock_initialize.return_value = {
        "authorization_url": "https://paystack.test/checkout/abc",
        "access_code": "access-123",
        "reference": "T211398129069938",
    }

    response = client.post(
        "/api/payments/initialize/",
        {"plan_id": str(plan.id), "full_name": "John Buyer", "mobile": "0241234567"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["authorization_url"] == "https://paystack.test/checkout/abc"
    assert response.data["customer_mobile"] == "+233241234567"
    assert Payment.objects.filter(id=response.data["payment_id"], provider="paystack").exists()


@pytest.mark.django_db
@patch("payments.services.HubtelClient.send_sms")
@patch("payments.services.PaystackClient.verify_transaction")
def test_purchase_verify_api_returns_voucher_code(mock_verify, mock_send_sms):
    customer = CustomerFactory(phone="+233241234567")
    plan = PlanFactory(price=18)
    Payment.objects.create(
        customer=customer,
        plan=plan,
        amount=plan.price,
        provider="paystack",
        provider_reference="ANW-API-REF-1",
        status=PaymentStatus.PENDING,
    )
    mock_verify.return_value = {
        "status": "success",
        "amount": 1800,
        "currency": "GHS",
        "authorization": {},
        "customer": {},
    }
    mock_send_sms.return_value = (True, "")
    client = APIClient()

    response = client.get("/api/payments/verify/?reference=ANW-API-REF-1")

    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["voucher_code"].startswith("ANW-PUR-")
