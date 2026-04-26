from celery import shared_task

from sessions.models import Entitlement

from .services import sync_entitlement_to_radius, sync_radacct_records


@shared_task
def sync_entitlement_task(entitlement_id: str) -> None:
    entitlement = Entitlement.objects.select_related("customer", "plan", "plan__speed_profile").get(id=entitlement_id)
    if entitlement.customer:
        cleartext_password = entitlement.voucher.code if entitlement.voucher else "temporary-password"
        sync_entitlement_to_radius(
            username=entitlement.customer.username,
            cleartext_password=cleartext_password,
            entitlement=entitlement,
        )


@shared_task
def sync_radacct_task() -> int:
    return sync_radacct_records()
