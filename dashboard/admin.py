from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import KpiSnapshot


@admin.register(KpiSnapshot)
class KpiSnapshotAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("created_at", "active_sessions", "active_customers", "revenue_total")
