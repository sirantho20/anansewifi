from django.db import models

from core.models import BaseModel


class BillingType(models.TextChoices):
    VOUCHER = "voucher", "Voucher"
    DIRECT = "direct", "Direct"
    MANUAL = "manual", "Manual"


class QuotaType(models.TextChoices):
    DURATION = "duration", "Duration"
    DATA = "data", "Data"
    DURATION_AND_DATA = "duration_and_data", "Duration And Data"
    UNLIMITED = "unlimited", "Unlimited"


class SpeedProfile(BaseModel):
    name = models.CharField(max_length=64, unique=True)
    up_rate_kbps = models.PositiveIntegerField(default=1024)
    down_rate_kbps = models.PositiveIntegerField(default=1024)
    mikrotik_rate_limit = models.CharField(max_length=128, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.up_rate_kbps}/{self.down_rate_kbps} kbps)"


class Plan(BaseModel):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_type = models.CharField(
        max_length=16,
        choices=BillingType.choices,
        default=BillingType.VOUCHER,
    )
    quota_type = models.CharField(
        max_length=20,
        choices=QuotaType.choices,
        default=QuotaType.DURATION,
    )
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    data_bytes = models.BigIntegerField(null=True, blank=True)
    speed_profile = models.ForeignKey(
        SpeedProfile,
        on_delete=models.PROTECT,
        related_name="plans",
        null=True,
        blank=True,
    )
    concurrent_device_limit = models.PositiveSmallIntegerField(default=1)
    idle_timeout_seconds = models.PositiveIntegerField(default=600)
    session_timeout_seconds = models.PositiveIntegerField(default=3600)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"
