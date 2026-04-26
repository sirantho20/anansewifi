from django.db import models
from django.db.models import Q

from core.models import BaseModel


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class Payment(BaseModel):
    customer = models.ForeignKey("customers.Customer", on_delete=models.CASCADE, related_name="payments")
    plan = models.ForeignKey("plans.Plan", on_delete=models.SET_NULL, null=True, blank=True)
    voucher = models.ForeignKey("vouchers.Voucher", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    provider = models.CharField(max_length=32, default="manual")
    provider_reference = models.CharField(max_length=128, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_reference"],
                condition=~Q(provider_reference=""),
                name="uniq_payment_provider_reference",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.customer.username} - {self.amount}"
