import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from .factories import CustomerFactory, VoucherFactory


@pytest.mark.django_db
def test_sensitive_dashboards_require_staff(client):
    assert client.get("/dashboard/").status_code == 302
    assert client.get("/dashboard/sessions/").status_code == 302
    assert client.get("/dashboard/auth-issues/").status_code == 302

    user = get_user_model().objects.create_user(
        username="staff-ops",
        password="pass12345",
        is_staff=True,
    )
    client.force_login(user)
    assert client.get("/dashboard/").status_code == 200


@pytest.mark.django_db
def test_sensitive_api_endpoints_require_admin_permissions():
    customer = CustomerFactory(username="secure-user")
    VoucherFactory()
    api_client = APIClient()

    assert api_client.get("/api/dashboard/summary/").status_code == 403
    assert api_client.get("/api/customers/").status_code == 403
    assert api_client.get("/api/sessions/").status_code == 403
    assert api_client.get("/api/vouchers/").status_code == 403

    redeem_response = api_client.post(
        "/api/vouchers/redeem/",
        {"code": "ANW-DOES-NOT-EXIST", "username": customer.username},
        format="json",
    )
    assert redeem_response.status_code == 404

    admin_user = get_user_model().objects.create_user(
        username="admin-api",
        password="pass12345",
        is_staff=True,
    )
    api_client.force_authenticate(user=admin_user)
    assert api_client.get("/api/dashboard/summary/").status_code == 200
    assert api_client.get("/api/customers/").status_code == 200
    assert api_client.get("/api/sessions/").status_code == 200
    assert api_client.get("/api/vouchers/").status_code == 200


@pytest.mark.django_db
@override_settings(RADIUS_ACCOUNTING_INGEST_TOKEN="radius-secret")
def test_radius_accounting_ingest_requires_token_when_configured():
    payload = {
        "event_type": "interim",
        "username": "token-user",
        "session_id": "sess-token-1",
        "input_octets": 10,
        "output_octets": 30,
        "duration_seconds": 5,
    }
    api_client = APIClient()

    assert api_client.post("/api/radius/accounting/", payload, format="json").status_code == 401
    assert (
        api_client.post(
            "/api/radius/accounting/",
            payload,
            format="json",
            HTTP_X_RADIUS_TOKEN="radius-secret",
        ).status_code
        == 200
    )

