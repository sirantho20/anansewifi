import pytest
from django.conf import settings

from plans.models import Plan
from tests.factories import PlanFactory

from .models import PaymentStatus
from .services import PaystackClient, PaymentProviderError, initialize_plan_purchase


pytestmark = pytest.mark.django_db


def _skip_if_live_paystack_not_configured() -> None:
    if not settings.PAYSTACK_SECRET_KEY:
        pytest.skip("PAYSTACK_SECRET_KEY is not configured for live integration tests.")


def _callback_url() -> str:
    return settings.PAYSTACK_CALLBACK_URL or "http://localhost:18080/portal/purchase/callback/"


def test_live_paystack_initialize_returns_checkout_data():
    _skip_if_live_paystack_not_configured()

    client = PaystackClient()
    result = client.initialize_transaction(
        email="live-test-paystack@example.com",
        amount_pesewas=500,
        callback_url=_callback_url(),
        metadata={"source": "anansewifi-live-integration"},
    )

    assert result["authorization_url"].startswith("https://")
    assert result["reference"]
    assert result["access_code"]


def test_live_paystack_verify_initialized_reference_returns_transaction():
    _skip_if_live_paystack_not_configured()

    client = PaystackClient()
    init = client.initialize_transaction(
        email="live-test-paystack@example.com",
        amount_pesewas=500,
        callback_url=_callback_url(),
        metadata={"source": "anansewifi-live-integration"},
    )
    reference = init["reference"]

    verified = client.verify_transaction(reference)

    assert verified["reference"] == reference
    assert verified.get("status")
    assert "amount" in verified


def test_live_paystack_verify_invalid_reference_raises_provider_error():
    _skip_if_live_paystack_not_configured()

    client = PaystackClient()
    reference = "invalid-ref-that-does-not-exist-00000000"

    with pytest.raises(PaymentProviderError):
        client.verify_transaction(reference)


def test_live_initialize_plan_purchase_creates_pending_payment():
    _skip_if_live_paystack_not_configured()

    plan = Plan.objects.filter(is_active=True).first() or PlanFactory(price=15)
    purchase = initialize_plan_purchase(
        plan=plan,
        full_name="Live Integration Customer",
        mobile="0241112233",
    )

    purchase.payment.refresh_from_db()
    assert purchase.payment.status == PaymentStatus.PENDING
    assert purchase.authorization_url.startswith("https://")
    assert purchase.reference == purchase.payment.provider_reference
