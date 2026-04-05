"""Admin configuration for routes app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Route, Waypoint


class WaypointInline(admin.TabularInline):
    """Точки маршрута в админке."""

    model = Waypoint
    extra = 1
    fields = (
        "sequence",
        "point_type",
        "address",
        "order",
        "latitude",
        "longitude",
        "scheduled_arrival",
        "notes",
    )
    ordering = ("sequence",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    """Admin для маршрутов."""

    list_display = (
        "name",
        "status",
        "vehicle",
        "driver",
        "orders_count_display",
        "total_distance_km",
        "estimated_time_hours",
        "estimated_fuel_l",
        "departure_datetime",
        "is_active",
        "created_at",
    )
    list_filter = (
        "status",
        "is_active",
        "vehicle__vehicle_type",
        "created_at",
    )
    search_fields = (
        "name",
        "vehicle__plate_number",
        "driver__last_name",
        "driver__first_name",
    )
    readonly_fields = (
        "total_distance_km",
        "estimated_time_hours",
        "estimated_fuel_l",
        "estimated_completion_datetime",
        "completed_at",
        "created_at",
        "updated_at",
        "load_info",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    fieldsets = (
        (
            None,
            {"fields": ("name", "status")},
        ),
        (
            _("Исполнители"),
            {
                "fields": (
                    "vehicle",
                    "driver",
                    "orders",
                ),
            },
        ),
        (
            _("Время"),
            {
                "fields": (
                    "departure_datetime",
                    "estimated_completion_datetime",
                    "completed_at",
                ),
            },
        ),
        (
            _("Параметры маршрута"),
            {
                "fields": (
                    "total_distance_km",
                    "estimated_time_hours",
                    "estimated_fuel_l",
                    "actual_distance_km",
                    "actual_fuel_l",
                    "load_info",
                ),
            },
        ),
        (
            _("Примечания"),
            {"fields": ("notes", "is_active")},
        ),
        (
            _("Системные поля"),
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
    filter_horizontal = ("orders",)
    inlines = [WaypointInline]

    @admin.display(description="Заказы")
    def orders_count_display(self, obj):
        return f"{obj.orders.count()} шт."

    @admin.display(description="Загрузка ТС")
    def load_info(self, obj):
        errors = obj.validate_load()
        lines = [
            f"Вес: {obj.total_weight_kg:.0f} / {obj.vehicle.capacity_kg:.0f} кг ({obj.load_percentage_weight}%)",
            f"Объём: {obj.total_volume_m3:.1f} / {obj.vehicle.volume_m3:.1f} м³ ({obj.load_percentage_volume}%)",
        ]
        if errors:
            lines.append("⚠ " + "; ".join(errors))
        return "\n".join(lines)


@admin.register(Waypoint)
class WaypointAdmin(admin.ModelAdmin):
    """Admin для точек маршрута."""

    list_display = (
        "sequence",
        "route",
        "point_type",
        "address",
        "order",
        "latitude",
        "longitude",
        "scheduled_arrival",
        "visited",
    )
    list_filter = ("point_type", "visited")
    search_fields = ("address", "notes")
    ordering = ("route", "sequence")
