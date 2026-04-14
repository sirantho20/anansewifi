from django.db import models

from core.models import BaseModel


class AuditLog(BaseModel):
    actor = models.CharField(max_length=120)
    action = models.CharField(max_length=120)
    target_type = models.CharField(max_length=120)
    target_id = models.CharField(max_length=64)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(protocol="IPv4", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.actor}:{self.action}"
