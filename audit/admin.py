from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("actor", "action", "target_type", "target_id", "created_at")
    search_fields = ("actor", "action", "target_type", "target_id")
