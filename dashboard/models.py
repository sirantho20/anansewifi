from django.db import models

from core.models import BaseModel


class KpiSnapshot(BaseModel):
    active_sessions = models.PositiveIntegerField(default=0)
    active_customers = models.PositiveIntegerField(default=0)
    revenue_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]
