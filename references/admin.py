"""Admin configuration for references app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Client, CargoType, FuelNorm


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin for Client model."""

    list_display = (
        "name",
        "inn",
        "contact_person",
        "contact_phone",
        "contract_number",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "inn", "contact_person", "contact_email", "contract_number")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("name",)
    fieldsets = (
        (
            _("Основная информация"),
            {"fields": ("name", "inn", "legal_address", "is_active")},
        ),
        (
            _("Контактные данные"),
            {"fields": ("contact_person", "contact_phone", "contact_email")},
        ),
        (
            _("Договор"),
            {"fields": ("contract_number", "contract_date")},
        ),
        (
            _("Системные поля"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(CargoType)
class CargoTypeAdmin(admin.ModelAdmin):
    """Admin for CargoType model."""

    list_display = ("name", "hazard_class", "description")
    list_filter = ("hazard_class",)
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(FuelNorm)
class FuelNormAdmin(admin.ModelAdmin):
    """Admin for FuelNorm model."""

    list_display = (
        "vehicle_type",
        "consumption_city",
        "consumption_highway",
        "consumption_winter",
        "valid_from",
        "valid_to",
    )
    list_filter = ("vehicle_type", "valid_from")
    search_fields = ("vehicle_type",)
    readonly_fields = ("valid_from",)
    ordering = ("-valid_from",)
