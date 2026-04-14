from django.contrib import admin

from .models import KpiSnapshot


@admin.register(KpiSnapshot)
class KpiSnapshotAdmin(admin.ModelAdmin):
    list_display = ("created_at", "active_sessions", "active_customers", "revenue_total")
