from django.db import transaction

from sessions.models import Entitlement
from sessions.services import ingest_accounting_event

from .models import RadAcct, RadAcctSyncState, RadCheck, RadReply


class RadiusProjectionService:
    @staticmethod
    @transaction.atomic
    def sync_entitlement(entitlement: Entitlement, cleartext_password: str) -> None:
        if not entitlement.customer_id:
            return

        username = entitlement.customer.username
        plan = entitlement.plan
        RadCheck.objects.filter(username=username).delete()
        RadReply.objects.filter(username=username).delete()

        RadCheck.objects.create(
            username=username,
            attribute="Cleartext-Password",
            value=cleartext_password,
        )
        if plan.speed_profile and plan.speed_profile.mikrotik_rate_limit:
            RadReply.objects.create(
                username=username,
                attribute="Mikrotik-Rate-Limit",
                value=plan.speed_profile.mikrotik_rate_limit,
            )
        RadReply.objects.create(
            username=username,
            attribute="Session-Timeout",
            value=str(plan.session_timeout_seconds),
        )
        RadReply.objects.create(
            username=username,
            attribute="Idle-Timeout",
            value=str(plan.idle_timeout_seconds),
        )

    @staticmethod
    @transaction.atomic
    def disable_identity(username: str) -> None:
        RadCheck.objects.filter(username=username).delete()
        RadReply.objects.filter(username=username).delete()


def sync_entitlement_to_radius(username: str, cleartext_password: str, entitlement: Entitlement) -> None:
    if entitlement.customer and entitlement.customer.username != username:
        username = entitlement.customer.username
    RadiusProjectionService.sync_entitlement(entitlement=entitlement, cleartext_password=cleartext_password)


@transaction.atomic
def sync_radacct_records() -> int:
    sync_state, _ = RadAcctSyncState.objects.select_for_update().get_or_create(id=1)
    queryset = RadAcct.objects.filter(radacctid__gt=sync_state.last_radacctid).order_by("radacctid")
    processed = 0

    for record in queryset:
        event_type = "interim"
        if record.acctstoptime:
            event_type = "stop"
        elif record.acctstarttime and not record.acctupdatetime:
            event_type = "start"

        payload = {
            "event_type": event_type,
            "username": record.username,
            "session_id": record.acctsessionid,
            "framed_ip_address": record.framedipaddress,
            "calling_station_id": record.callingstationid,
            "nas_ip_address": record.nasipaddress,
            "input_octets": record.acctinputoctets,
            "output_octets": record.acctoutputoctets,
            "duration_seconds": record.acctsessiontime or 0,
            "terminate_cause": record.acctterminatecause,
            "radacct_id": record.radacctid,
            "acctuniqueid": record.acctuniqueid,
        }
        ingest_accounting_event(payload)
        sync_state.last_radacctid = record.radacctid
        processed += 1

    if processed:
        sync_state.save(update_fields=["last_radacctid", "updated_at"])

    return processed
