from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import AccountingRecord, Entitlement, Session


@admin.register(Entitlement)
class EntitlementAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("customer", "plan", "status", "start_at", "end_at")
    list_filter = ("status", "plan")
    search_fields = ("customer__username", "plan__name", "voucher__code")
    autocomplete_fields = ("customer", "voucher", "plan")


@admin.register(Session)
class SessionAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("session_id", "username", "mac_address", "status", "started_at", "ended_at")
    list_filter = ("status",)
    search_fields = ("session_id", "username", "mac_address")
    autocomplete_fields = ("customer", "entitlement", "nas")


@admin.register(AccountingRecord)
class AccountingRecordAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("event_type", "username", "session_id", "happened_at")
    list_filter = ("event_type",)
    search_fields = ("username", "session_id", "calling_station_id")
    autocomplete_fields = ("linked_session",)
