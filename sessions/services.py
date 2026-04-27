from django.db import transaction

from customers.models import Customer
from network.models import NASDevice
from vouchers.models import Voucher

from .models import AccountingRecord, Session


@transaction.atomic
def ingest_accounting_event(payload: dict) -> AccountingRecord:
    session, _ = Session.objects.get_or_create(
        session_id=payload["session_id"],
        defaults={
            "username": payload["username"],
            "mac_address": payload.get("calling_station_id", ""),
            "ip_address": payload.get("framed_ip_address"),
        },
    )
    session_update_fields = []
    if payload.get("nas_ip_address"):
        nas = NASDevice.objects.filter(ip_address=payload["nas_ip_address"]).first()
        if nas:
            session.nas = nas
            session_update_fields.append("nas")
    if not session.customer:
        un = payload["username"]
        customer = Customer.objects.filter(username=un).first()
        if not customer:
            voucher = (
                Voucher.objects.filter(code=un).select_related("redeemed_by").first()
            )
            if voucher and voucher.redeemed_by_id:
                customer = voucher.redeemed_by
        if customer:
            session.customer = customer
            session_update_fields.append("customer")
    if session_update_fields:
        session.save(update_fields=[*session_update_fields, "updated_at"])
    session.update_usage(
        input_octets=payload.get("input_octets", 0),
        output_octets=payload.get("output_octets", 0),
        duration_seconds=payload.get("duration_seconds", 0),
    )
    if payload.get("event_type") == "stop":
        session.close(reason=payload.get("terminate_cause", "acct-stop"))
    record = AccountingRecord.objects.create(
        event_type=payload["event_type"],
        username=payload["username"],
        session_id=payload["session_id"],
        framed_ip_address=payload.get("framed_ip_address"),
        calling_station_id=payload.get("calling_station_id", ""),
        nas_ip_address=payload.get("nas_ip_address"),
        input_octets=payload.get("input_octets", 0),
        output_octets=payload.get("output_octets", 0),
        duration_seconds=payload.get("duration_seconds", 0),
        linked_session=session,
        raw_payload=payload,
    )
    return record
