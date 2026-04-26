from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import NASDevice, RadiusClient, Site


@admin.register(Site)
class SiteAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("name", "hotspot_subnet", "management_subnet", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(NASDevice)
class NASDeviceAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("name", "site", "ip_address", "is_active")
    search_fields = ("name", "ip_address", "site__name")
    list_filter = ("is_active",)
    autocomplete_fields = ("site",)


@admin.register(RadiusClient)
class RadiusClientAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("identifier", "nas", "enabled")
    search_fields = ("identifier", "shortname", "nas__name")
    list_filter = ("enabled",)
    autocomplete_fields = ("nas",)
