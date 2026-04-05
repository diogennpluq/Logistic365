"""Admin configuration for transport app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Driver, TripLog, Vehicle, VehicleStatus, VehicleType


class TripLogInline(admin.TabularInline):
    """Inline for TripLog entries within Vehicle admin."""

    model = TripLog
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("driver", "departure_date", "arrival_date", "mileage", "fuel_consumed", "created_at")
    ordering = ("-departure_date",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin for Vehicle model."""

    list_display = (
        "plate_number",
        "vehicle_type",
        "brand",
        "model",
        "capacity_kg",
        "fuel_consumption",
        "status",
        "next_maintenance",
        "created_at",
    )
    list_filter = ("vehicle_type", "status", "next_maintenance")
    search_fields = ("plate_number", "brand", "model")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("plate_number",)
    inlines = [TripLogInline]
    fieldsets = (
        (
            _("Основная информация"),
            {"fields": ("plate_number", "vehicle_type", "brand", "model", "status")},
        ),
        (
            _("Характеристики"),
            {
                "fields": (
                    "capacity_kg",
                    "volume_m3",
                    "current_mileage",
                    "fuel_consumption",
                )
            },
        ),
        (
            _("Обслуживание"),
            {"fields": ("next_maintenance", "notes")},
        ),
        (
            _("Системные поля"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    """Admin for Driver model."""

    list_display = (
        "last_name",
        "first_name",
        "patronymic",
        "phone",
        "license_number",
        "license_category",
        "vehicle",
        "is_active",
        "medical_exam_date",
    )
    list_filter = ("is_active", "license_category", "vehicle")
    search_fields = ("last_name", "first_name", "patronymic", "phone", "license_number")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("last_name", "first_name")
    fieldsets = (
        (
            _("Персональные данные"),
            {
                "fields": (
                    "last_name",
                    "first_name",
                    "patronymic",
                    "phone",
                    "is_active",
                )
            },
        ),
        (
            _("Водительское удостоверение"),
            {"fields": ("license_number", "license_category", "medical_exam_date")},
        ),
        (
            _("Закреплённое ТС"),
            {"fields": ("vehicle",)},
        ),
        (
            _("Системные поля"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(TripLog)
class TripLogAdmin(admin.ModelAdmin):
    """Admin for TripLog model."""

    list_display = (
        "driver",
        "vehicle",
        "departure_date",
        "arrival_date",
        "mileage",
        "fuel_consumed",
        "created_at",
    )
    list_filter = ("driver", "vehicle", "departure_date")
    search_fields = ("driver__last_name", "driver__first_name", "vehicle__plate_number", "notes")
    readonly_fields = ("created_at",)
    ordering = ("-departure_date",)
    date_hierarchy = "departure_date"
    fieldsets = (
        (
            _("Рейс"),
            {"fields": ("driver", "vehicle", "departure_date", "arrival_date")},
        ),
        (
            _("Показатели"),
            {"fields": ("mileage", "fuel_consumed")},
        ),
        (
            _("Примечания"),
            {"fields": ("notes", "created_at")},
        ),
    )
