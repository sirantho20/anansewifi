import base64
import io
import json
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import pytest
from django.test import override_settings

from tests.factories import CustomerFactory, PlanFactory

from .models import Payment, PaymentStatus
from .services import (
    HubtelClient,
    PaymentProviderError,
    PaystackClient,
    initialize_plan_purchase,
    verify_plan_purchase,
)


@pytest.mark.django_db
@patch("payments.services.PaystackClient.initialize_transaction")
def test_initialize_plan_purchase_creates_pending_payment(mock_initialize):
    plan = PlanFactory(price=15)
    mock_initialize.return_value = {
        "authorization_url": "https://paystack.test/checkout/ref",
        "access_code": "ACCESS-1",
        "reference": "T211398129069938",
    }

    result = initialize_plan_purchase(
        plan=plan,
        full_name="Portal Buyer",
        mobile="0241234567",
    )

    payment = Payment.objects.get(id=result.payment.id)
    assert result.customer.phone == "+233241234567"
    assert payment.status == PaymentStatus.PENDING
    assert payment.provider == "paystack"
    assert payment.provider_reference == "T211398129069938"
    assert result.reference == "T211398129069938"
    assert result.authorization_url.startswith("https://paystack.test")


@pytest.mark.django_db
@patch("payments.services.HubtelClient.send_sms")
@patch("payments.services.PaystackClient.verify_transaction")
def test_verify_plan_purchase_marks_success_and_issues_voucher(mock_verify, mock_send_sms):
    customer = CustomerFactory(phone="+233241234567")
    plan = PlanFactory(price=20)
    payment = Payment.objects.create(
        customer=customer,
        plan=plan,
        amount=plan.price,
        provider="paystack",
        provider_reference="ANW-TEST-REF-1",
    )
    mock_verify.return_value = {
        "status": "success",
        "amount": 2000,
        "currency": "GHS",
        "authorization": {"channel": "card"},
        "customer": {"email": "buyer@test.local"},
    }
    mock_send_sms.return_value = (True, "")

    result = verify_plan_purchase("ANW-TEST-REF-1")
    payment.refresh_from_db()

    assert result.voucher is not None
    assert payment.status == PaymentStatus.SUCCESS
    assert payment.voucher_id == result.voucher.id
    assert result.sms_sent is True


@pytest.mark.django_db
@patch("payments.services.HubtelClient.send_sms")
@patch("payments.services.PaystackClient.verify_transaction")
def test_verify_plan_purchase_is_idempotent(mock_verify, mock_send_sms):
    customer = CustomerFactory(phone="+233241234567")
    plan = PlanFactory(price=10)
    payment = Payment.objects.create(
        customer=customer,
        plan=plan,
        amount=plan.price,
        provider="paystack",
        provider_reference="ANW-TEST-REF-2",
        status=PaymentStatus.PENDING,
    )
    mock_verify.return_value = {
        "status": "success",
        "amount": 1000,
        "currency": "GHS",
        "authorization": {},
        "customer": {},
    }
    mock_send_sms.return_value = (True, "")

    first_result = verify_plan_purchase("ANW-TEST-REF-2")
    second_result = verify_plan_purchase("ANW-TEST-REF-2")
    payment.refresh_from_db()

    assert payment.status == PaymentStatus.SUCCESS
    assert first_result.voucher.id == second_result.voucher.id


@pytest.mark.django_db
@patch("payments.services.PaystackClient.initialize_transaction")
def test_initialize_plan_purchase_persists_structured_provider_error(mock_initialize):
    plan = PlanFactory(price=15)
    mock_initialize.side_effect = PaymentProviderError(
        "Error occurred",
        http_status=403,
        code="1010",
        error_type="api_error",
        meta={"nextStep": "Try again later"},
    )

    with pytest.raises(PaymentProviderError):
        initialize_plan_purchase(
            plan=plan,
            full_name="Portal Buyer",
            mobile="0241234567",
        )

    payment = Payment.objects.latest("created_at")
    assert payment.status == PaymentStatus.FAILED
    assert payment.metadata["initialize_error"] == "Error occurred"
    assert payment.metadata["paystack_initialize_error"] == {
        "provider": "paystack",
        "message": "Error occurred",
        "http_status": 403,
        "code": "1010",
        "type": "api_error",
        "meta": {"nextStep": "Try again later"},
    }


@override_settings(PAYSTACK_SECRET_KEY="sk_test_123")
@patch("payments.services.requests.post")
def test_paystack_client_parses_http_error_payload(mock_post):
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 403
    mock_response.content = b"{}"
    mock_response.text = '{"status":false,"message":"Error occurred","type":"api_error","code":"1010","meta":{"nextStep":"Try again later"}}'
    mock_response.json.return_value = {
        "status": False,
        "message": "Error occurred",
        "type": "api_error",
        "code": "1010",
        "meta": {"nextStep": "Try again later"},
    }
    mock_post.return_value = mock_response

    client = PaystackClient()
    with pytest.raises(PaymentProviderError) as excinfo:
        client.initialize_transaction(
            email="buyer@example.com",
            amount_pesewas=500,
            callback_url="http://localhost/callback",
            metadata={"probe": True},
        )

    provider_error = excinfo.value
    assert str(provider_error) == "Error occurred"
    assert provider_error.http_status == 403
    assert provider_error.code == "1010"
    assert provider_error.error_type == "api_error"
    assert provider_error.meta == {"nextStep": "Try again later"}


@override_settings(
    HUBTEL_CLIENT_ID="client-1",
    HUBTEL_CLIENT_SECRET="secret-1",
    HUBTEL_SENDER_ID="Ananse",
    HUBTEL_BASE_URL="https://smsc.hubtel.com",
    HUBTEL_SMS_SEND_PATH="/v1/messages/send",
    HUBTEL_TIMEOUT_SECONDS=9,
)
@patch("payments.services.request.urlopen")
def test_hubtel_send_sms_uses_basic_auth_and_expected_payload(mock_urlopen):
    response = Mock()
    response.read.return_value = b'{"Status":"0"}'
    response.status = 200
    mock_urlopen.return_value.__enter__.return_value = response

    client = HubtelClient()
    sent, error_message = client.send_sms(to_number="+233241234567", message="Voucher is ANW123")

    assert sent is True
    assert error_message == ""
    mock_urlopen.assert_called_once()
    req = mock_urlopen.call_args.args[0]
    timeout = mock_urlopen.call_args.kwargs["timeout"]
    assert timeout == 9
    assert req.full_url == "https://smsc.hubtel.com/v1/messages/send"

    auth_header = req.get_header("Authorization")
    assert auth_header and auth_header.startswith("Basic ")
    decoded = base64.b64decode(auth_header.split(" ", 1)[1]).decode("utf-8")
    assert decoded == "client-1:secret-1"

    payload = json.loads(req.data.decode("utf-8"))
    assert payload == {
        "From": "Ananse",
        "To": "+233241234567",
        "Content": "Voucher is ANW123",
        "RegisteredDelivery": True,
    }


@override_settings(
    HUBTEL_CLIENT_ID="",
    HUBTEL_CLIENT_SECRET="",
)
def test_hubtel_send_sms_fails_when_credentials_missing():
    client = HubtelClient()
    sent, error_message = client.send_sms(to_number="+233241234567", message="test")
    assert sent is False
    assert error_message == "Hubtel credentials are missing."


@override_settings(
    HUBTEL_CLIENT_ID="client-1",
    HUBTEL_CLIENT_SECRET="secret-1",
    HUBTEL_SENDER_ID="Ananse",
    HUBTEL_BASE_URL="https://smsc.hubtel.com",
)
@patch("payments.services.request.urlopen")
def test_hubtel_send_sms_surfaces_http_error_message(mock_urlopen):
    request_error = HTTPError(
        url="https://smsc.hubtel.com/v1/messages/send",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=io.BytesIO(b'{"Message":"Invalid sender ID"}'),
    )
    mock_urlopen.side_effect = request_error

    client = HubtelClient()
    sent, error_message = client.send_sms(to_number="+233241234567", message="test")

    assert sent is False
    assert "Hubtel HTTP error:" in error_message
    assert "Invalid sender ID" in error_message
