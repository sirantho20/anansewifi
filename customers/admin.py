from django.contrib import admin

from .models import Customer, Device


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("username", "full_name", "phone", "is_active")
    search_fields = ("username", "full_name", "phone", "email")
    list_filter = ("is_active",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("customer", "mac_address", "is_trusted")
    search_fields = ("mac_address", "customer__username")
    list_filter = ("is_trusted",)
