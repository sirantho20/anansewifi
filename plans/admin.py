from django.contrib import admin

from .models import Plan, SpeedProfile


@admin.register(SpeedProfile)
class SpeedProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "up_rate_kbps", "down_rate_kbps")
    search_fields = ("name", "code")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price", "billing_type", "quota_type", "is_active")
    list_filter = ("billing_type", "quota_type", "is_active")
    search_fields = ("name", "code")
