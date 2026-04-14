from django.contrib import admin

from .models import NASDevice, RadiusClient, Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "hotspot_subnet", "management_subnet", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(NASDevice)
class NASDeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "site", "ip_address", "is_active")
    search_fields = ("name", "ip_address", "site__name")
    list_filter = ("is_active",)


@admin.register(RadiusClient)
class RadiusClientAdmin(admin.ModelAdmin):
    list_display = ("identifier", "nas", "enabled")
    search_fields = ("identifier", "shortname", "nas__name")
    list_filter = ("enabled",)
