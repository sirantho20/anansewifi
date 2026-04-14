from django.db import models

from core.models import BaseModel


class Site(BaseModel):
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=40, unique=True)
    hotspot_subnet = models.CharField(max_length=32, blank=True)
    management_subnet = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class NASDevice(BaseModel):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="nas_devices")
    name = models.CharField(max_length=80)
    ip_address = models.GenericIPAddressField(protocol="IPv4")
    secret = models.CharField(max_length=128)
    shortname = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("site", "ip_address")
        ordering = ["site__name", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"


class RadiusClient(BaseModel):
    nas = models.ForeignKey(NASDevice, on_delete=models.CASCADE, related_name="radius_clients")
    identifier = models.CharField(max_length=80, unique=True)
    shared_secret = models.CharField(max_length=128)
    shortname = models.CharField(max_length=64, blank=True)
    enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.identifier
