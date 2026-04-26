from django.contrib import admin

from core.admin_ecosystem import EcosystemSummaryAdminMixin

from .models import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(EcosystemSummaryAdminMixin, admin.ModelAdmin):
    list_display = ("user", "role", "is_active")
    search_fields = ("user__username", "role")
    autocomplete_fields = ("user",)
