from django.db import models
from django.utils import timezone

from core.models import BaseModel


class EntitlementStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    CONSUMED = "consumed", "Consumed"


class SessionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"
    REJECTED = "rejected", "Rejected"


class Entitlement(BaseModel):
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        related_name="entitlements",
        null=True,
        blank=True,
    )
    voucher = models.ForeignKey(
        "vouchers.Voucher",
        on_delete=models.SET_NULL,
        related_name="entitlements",
        null=True,
        blank=True,
    )
    plan = models.ForeignKey("plans.Plan", on_delete=models.PROTECT, related_name="entitlements")
    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)
    remaining_data_bytes = models.BigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=EntitlementStatus.choices, default=EntitlementStatus.PENDING)

    class Meta:
        ordering = ["-created_at"]

    def activate(self) -> None:
        self.status = EntitlementStatus.ACTIVE
        self.save(update_fields=["status", "updated_at"])

    def __str__(self) -> str:
        owner = self.customer.username if self.customer else "voucher"
        return f"{owner}:{self.plan_id}"


class Session(BaseModel):
    customer = models.ForeignKey("customers.Customer", on_delete=models.SET_NULL, null=True, blank=True)
    entitlement = models.ForeignKey(Entitlement, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=128)
    mac_address = models.CharField(max_length=17)
    ip_address = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    nas = models.ForeignKey("network.NASDevice", on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=96, unique=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    input_octets = models.BigIntegerField(default=0)
    output_octets = models.BigIntegerField(default=0)
    total_octets = models.BigIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=12, choices=SessionStatus.choices, default=SessionStatus.ACTIVE)
    disconnect_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def update_usage(self, input_octets: int, output_octets: int, duration_seconds: int) -> None:
        self.input_octets = input_octets
        self.output_octets = output_octets
        self.total_octets = input_octets + output_octets
        self.duration_seconds = duration_seconds
        self.save(
            update_fields=[
                "input_octets",
                "output_octets",
                "total_octets",
                "duration_seconds",
                "updated_at",
            ]
        )

    def close(self, reason: str = "") -> None:
        self.status = SessionStatus.CLOSED
        self.ended_at = timezone.now()
        self.disconnect_reason = reason
        self.save(update_fields=["status", "ended_at", "disconnect_reason", "updated_at"])

    def __str__(self) -> str:
        return self.session_id


class AccountingRecord(BaseModel):
    event_type = models.CharField(max_length=16)
    username = models.CharField(max_length=128)
    session_id = models.CharField(max_length=96)
    framed_ip_address = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    calling_station_id = models.CharField(max_length=17, blank=True)
    nas_ip_address = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)
    input_octets = models.BigIntegerField(default=0)
    output_octets = models.BigIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=0)
    happened_at = models.DateTimeField(default=timezone.now)
    linked_session = models.ForeignKey(
        Session,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounting_records",
    )
    raw_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-happened_at"]

    def __str__(self) -> str:
        return f"{self.event_type}:{self.session_id}"
