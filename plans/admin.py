from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import Plan, SpeedProfile


@admin.register(SpeedProfile)
class SpeedProfileAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("name", "up_rate_kbps", "down_rate_kbps")
    search_fields = ("name",)


@admin.register(Plan)
class PlanAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("name", "price", "billing_type", "quota_type", "is_featured", "is_active")
    list_filter = ("billing_type", "quota_type", "is_featured", "is_active")
    search_fields = ("name",)
    autocomplete_fields = ("speed_profile",)
