import pytest

from sessions.models import Entitlement, EntitlementStatus
from vouchers.services import redeem_voucher

from .factories import CustomerFactory, VoucherFactory


@pytest.mark.django_db
def test_redeem_voucher_creates_entitlement():
    customer = CustomerFactory()
    voucher = VoucherFactory()

    result = redeem_voucher(voucher.code, customer, mac_address="AA:BB:CC:DD:EE:FF")

    voucher.refresh_from_db()
    assert voucher.status == "redeemed"
    assert voucher.redeemed_by == customer
    assert Entitlement.objects.filter(voucher=voucher).exists()
    assert result.entitlement.status == EntitlementStatus.ACTIVE


@pytest.mark.django_db
def test_redeem_voucher_normalizes_lowercase_code():
    customer = CustomerFactory()
    voucher = VoucherFactory()

    result = redeem_voucher(voucher.code.lower(), customer, mac_address="")

    voucher.refresh_from_db()
    assert voucher.status == "redeemed"
    assert result.entitlement.plan_id == voucher.plan_id
