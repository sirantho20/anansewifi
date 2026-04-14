from django.contrib import admin

from .models import AccountingRecord, Entitlement, Session


@admin.register(Entitlement)
class EntitlementAdmin(admin.ModelAdmin):
    list_display = ("customer", "plan", "status", "start_at", "end_at")
    list_filter = ("status", "plan")
    search_fields = ("customer__username", "plan__name")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "username", "mac_address", "status", "started_at", "ended_at")
    list_filter = ("status",)
    search_fields = ("session_id", "username", "mac_address")


@admin.register(AccountingRecord)
class AccountingRecordAdmin(admin.ModelAdmin):
    list_display = ("event_type", "username", "session_id", "happened_at")
    list_filter = ("event_type",)
    search_fields = ("username", "session_id", "calling_station_id")
