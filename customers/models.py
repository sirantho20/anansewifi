from django.db import models
from django.utils import timezone

from core.models import BaseModel


class Customer(BaseModel):
    username = models.CharField(max_length=64, unique=True)
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32, blank=True, null=True, unique=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["username"]

    def touch(self) -> None:
        self.last_seen_at = timezone.now()
        self.save(update_fields=["last_seen_at", "updated_at"])

    def __str__(self) -> str:
        return self.username


class Device(BaseModel):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="devices",
    )
    mac_address = models.CharField(max_length=17)
    description = models.CharField(max_length=120, blank=True)
    is_trusted = models.BooleanField(default=False)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("customer", "mac_address")
        ordering = ["mac_address"]

    def __str__(self) -> str:
        return f"{self.customer.username}:{self.mac_address}"
