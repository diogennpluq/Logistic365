"""Admin configuration for orders app."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderAttachment, OrderStatusLog, OrderStatus


class OrderAttachmentInline(admin.TabularInline):
    """Inline for Order attachments."""

    model = OrderAttachment
    extra = 0
    readonly_fields = ("uploaded_at",)
    fields = ("file", "description", "uploaded_at")


class OrderStatusLogInline(admin.TabularInline):
    """Inline for Order status logs."""

    model = OrderStatusLog
    extra = 0
    readonly_fields = ("old_status", "new_status", "comment", "changed_by", "changed_at")
    fields = ("old_status", "new_status", "comment", "changed_by", "changed_at")
    can_delete = False
    ordering = ("-changed_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order model."""

    list_display = (
        "order_number",
        "client",
        "cargo_name",
        "cargo_type",
        "status",
        "vehicle",
        "driver",
        "loading_datetime",
        "required_delivery_datetime",
        "created_at",
    )
    list_filter = (
        "status",
        "cargo_type",
        "client",
        "vehicle",
        "driver",
        "hazard_class",
        "created_at",
    )
    search_fields = (
        "order_number",
        "cargo_name",
        "client__name",
        "loading_address",
        "unloading_address",
    )
    readonly_fields = ("order_number", "created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    inlines = [OrderStatusLogInline, OrderAttachmentInline]
    fieldsets = (
        (
            _("Основная информация"),
            {"fields": ("order_number", "client", "cargo_name", "cargo_type", "status")},
        ),
        (
            _("Характеристики груза"),
            {
                "fields": (
                    "cargo_weight_kg",
                    "cargo_volume_m3",
                    "hazard_class",
                    "special_conditions",
                )
            },
        ),
        (
            _("Адреса и даты"),
            {
                "fields": (
                    "loading_address",
                    "unloading_address",
                    "loading_datetime",
                    "required_delivery_datetime",
                )
            },
        ),
        (
            _("Исполнители"),
            {"fields": ("vehicle", "driver", "created_by")},
        ),
        (
            _("Документы"),
            {"fields": ("documents",)},
        ),
        (
            _("Системные поля"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    """Admin for OrderStatusLog model."""

    list_display = ("order", "old_status", "new_status", "changed_by", "changed_at")
    list_filter = ("old_status", "new_status", "changed_at")
    search_fields = ("order__order_number", "comment", "changed_by__username")
    readonly_fields = ("order", "old_status", "new_status", "comment", "changed_by", "changed_at")
    ordering = ("-changed_at",)
    date_hierarchy = "changed_at"


@admin.register(OrderAttachment)
class OrderAttachmentAdmin(admin.ModelAdmin):
    """Admin for OrderAttachment model."""

    list_display = ("order", "description", "uploaded_at")
    list_filter = ("uploaded_at",)
    search_fields = ("order__order_number", "description")
    readonly_fields = ("uploaded_at",)
    ordering = ("-uploaded_at",)
