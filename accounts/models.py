from django.db import models

from core.models import BaseModel


class StaffProfile(BaseModel):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="staff_profile")
    role = models.CharField(max_length=32, default="operator")
    phone = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.user.username}:{self.role}"
