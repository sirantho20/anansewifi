from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import Plan, SpeedProfile


@admin.register(SpeedProfile)
class SpeedProfileAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("name", "up_rate_kbps", "down_rate_kbps")
    search_fields = ("name",)


@admin.register(Plan)
class PlanAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "billing_type",
        "quota_type",
        "duration_minutes",
        "concurrent_device_limit",
        "is_featured",
        "is_active",
    )
    list_filter = ("billing_type", "quota_type", "is_featured", "is_active")
    search_fields = ("name",)
    autocomplete_fields = ("speed_profile",)
    fieldsets = (
        (
            "Basic",
            {
                "fields": (
                    "name",
                    "description",
                    "price",
                    "billing_type",
                    "is_active",
                    "is_featured",
                ),
            },
        ),
        (
            "Quota",
            {
                "fields": (
                    "quota_type",
                    "duration_minutes",
                    "data_bytes",
                ),
            },
        ),
        (
            "Speed profile",
            {
                "fields": ("speed_profile",),
            },
        ),
        (
            "Device and session limits",
            {
                "fields": (
                    "concurrent_device_limit",
                    "idle_timeout_seconds",
                    "session_timeout_seconds",
                ),
            },
        ),
    )
