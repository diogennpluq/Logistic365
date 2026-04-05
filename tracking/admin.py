"""Admin configuration for tracking app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import EventType, TrackingEvent, Waybill, WaybillAttachment


class WaybillAttachmentInline(admin.TabularInline):
    """Inline for Waybill attachments."""

    model = WaybillAttachment
    extra = 0
    readonly_fields = ("uploaded_at",)
    fields = ("file", "doc_type", "uploaded_at")


@admin.register(TrackingEvent)
class TrackingEventAdmin(admin.ModelAdmin):
    """Admin for TrackingEvent model."""

    list_display = (
        "order",
        "event_type",
        "timestamp",
        "latitude",
        "longitude",
        "recorded_by",
    )
    list_filter = ("event_type", "timestamp")
    search_fields = (
        "order__order_number",
        "comment",
        "recorded_by__username",
    )
    readonly_fields = ("timestamp",)
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"
    fieldsets = (
        (
            _("Событие"),
            {"fields": ("order", "event_type", "timestamp")},
        ),
        (
            _("Геолокация"),
            {"fields": ("latitude", "longitude")},
        ),
        (
            _("Дополнительно"),
            {"fields": ("comment", "recorded_by")},
        ),
    )


@admin.register(Waybill)
class WaybillAdmin(admin.ModelAdmin):
    """Admin for Waybill model."""

    list_display = (
        "number",
        "order",
        "driver",
        "vehicle",
        "issue_date",
        "valid_until",
        "fuel_issued",
        "fuel_returned",
        "is_closed",
        "created_at",
    )
    list_filter = ("is_closed", "issue_date", "vehicle", "driver")
    search_fields = (
        "number",
        "order__order_number",
        "driver__last_name",
        "driver__first_name",
        "vehicle__plate_number",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-issue_date",)
    date_hierarchy = "issue_date"
    inlines = [WaybillAttachmentInline]
    fieldsets = (
        (
            _("Основная информация"),
            {"fields": ("number", "order", "issue_date", "valid_until", "is_closed")},
        ),
        (
            _("Исполнители"),
            {"fields": ("driver", "vehicle")},
        ),
        (
            _("Маршрут"),
            {"fields": ("route_description",)},
        ),
        (
            _("Топливо и пробег"),
            {
                "fields": (
                    "fuel_issued",
                    "fuel_returned",
                    "mileage_start",
                    "mileage_end",
                )
            },
        ),
        (
            _("Системные поля"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(WaybillAttachment)
class WaybillAttachmentAdmin(admin.ModelAdmin):
    """Admin for WaybillAttachment model."""

    list_display = ("waybill", "doc_type", "uploaded_at")
    list_filter = ("doc_type", "uploaded_at")
    search_fields = ("waybill__number",)
    readonly_fields = ("uploaded_at",)
    ordering = ("-uploaded_at",)
