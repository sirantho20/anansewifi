from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from radius_integration.services import sync_entitlement_to_radius
from sessions.models import Entitlement

from .models import Voucher

if TYPE_CHECKING:
    from customers.models import Customer


@dataclass
class VoucherRedemptionResult:
    voucher: Voucher
    entitlement: Entitlement


def redeem_voucher(code: str, customer: "Customer", mac_address: str = "") -> VoucherRedemptionResult:
    with transaction.atomic():
        voucher = (
            Voucher.objects.select_related("plan")
            .select_for_update()
            .get(code=code)
        )
        if not voucher.is_valid():
            raise ValueError("Voucher is not valid.")
        if voucher.bound_mac and mac_address and voucher.bound_mac.lower() != mac_address.lower():
            raise ValueError("Voucher is bound to another device.")
        if not voucher.bound_mac and mac_address:
            voucher.bound_mac = mac_address

        now = timezone.now()
        plan = voucher.plan
        end_at = now
        if plan.duration_minutes:
            end_at = now + timezone.timedelta(minutes=plan.duration_minutes)

        entitlement = Entitlement.objects.create(
            customer=customer,
            voucher=voucher,
            plan=plan,
            start_at=now,
            end_at=end_at if plan.duration_minutes else None,
            remaining_data_bytes=plan.data_bytes,
        )
        entitlement.activate()
        sync_entitlement_to_radius(
            username=customer.username,
            cleartext_password=voucher.code,
            entitlement=entitlement,
        )
        voucher.mark_redeemed(customer)
        return VoucherRedemptionResult(voucher=voucher, entitlement=entitlement)
