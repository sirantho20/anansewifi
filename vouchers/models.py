from django.db import models
from django.utils import timezone
from typing import TYPE_CHECKING

from core.models import BaseModel

if TYPE_CHECKING:
    from customers.models import Customer


class VoucherStatus(models.TextChoices):
    AVAILABLE = "available", "Available"
    REDEEMED = "redeemed", "Redeemed"
    EXPIRED = "expired", "Expired"
    DISABLED = "disabled", "Disabled"


class VoucherBatch(BaseModel):
    name = models.CharField(max_length=128)
    code_prefix = models.CharField(max_length=12, default="ANW")
    plan = models.ForeignKey("plans.Plan", on_delete=models.PROTECT, related_name="voucher_batches")
    quantity = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class Voucher(BaseModel):
    code = models.CharField(max_length=48, unique=True)
    plan = models.ForeignKey("plans.Plan", on_delete=models.PROTECT, related_name="vouchers")
    status = models.CharField(
        max_length=16,
        choices=VoucherStatus.choices,
        default=VoucherStatus.AVAILABLE,
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    redeemed_by = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="redeemed_vouchers",
    )
    batch = models.ForeignKey(
        VoucherBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vouchers",
    )
    max_uses = models.PositiveIntegerField(default=1)
    use_count = models.PositiveIntegerField(default=0)
    bound_mac = models.CharField(max_length=17, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def mark_redeemed(self, customer: "Customer") -> None:
        self.status = VoucherStatus.REDEEMED
        self.redeemed_by = customer
        self.redeemed_at = timezone.now()
        self.use_count += 1
        self.save(update_fields=["status", "redeemed_by", "redeemed_at", "use_count", "updated_at"])

    def is_valid(self) -> bool:
        if self.status != VoucherStatus.AVAILABLE:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.use_count >= self.max_uses:
            return False
        return True

    def __str__(self) -> str:
        return self.code
