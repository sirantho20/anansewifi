import pytest

from plans.models import Plan


@pytest.mark.django_db
def test_portal_plans_page_lists_active_plan(client):
    Plan.objects.create(
        name="Portal Listed Plan",
        price="12.50",
        billing_type="voucher",
        quota_type="duration",
        duration_minutes=1440,
        is_active=True,
    )
    response = client.get("/portal/plans/")
    assert response.status_code == 200
    assert b"Portal Listed Plan" in response.content
    assert b"GHS" in response.content or b"12.50" in response.content
    assert "Choose your Wi‑Fi package" in response.content.decode()


@pytest.mark.django_db
def test_portal_plans_page_shows_featured_ribbon(client):
    Plan.objects.create(
        name="Regular",
        price="10.00",
        billing_type="voucher",
        quota_type="duration",
        duration_minutes=60,
        is_active=True,
        is_featured=False,
    )
    Plan.objects.create(
        name="Featured One",
        price="20.00",
        billing_type="voucher",
        quota_type="data",
        data_bytes=5 * 1024**3,
        is_active=True,
        is_featured=True,
    )
    response = client.get("/portal/plans/")
    assert response.status_code == 200
    assert b"POPULAR" in response.content
    assert b"Featured One" in response.content
