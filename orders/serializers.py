"""DRF Serializers for Orders app."""

from rest_framework import serializers

from .models import Order, OrderStatusLog, OrderAttachment


class OrderStatusLogSerializer(serializers.ModelSerializer):
    """Serializer for OrderStatusLog model."""

    class Meta:
        model = OrderStatusLog
        fields = "__all__"


class OrderAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for OrderAttachment model."""

    class Meta:
        model = OrderAttachment
        fields = "__all__"
        read_only_fields = ["uploaded_at"]


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model with nested status_logs and attachments."""

    status_logs = OrderStatusLogSerializer(many=True, read_only=True)
    attachments = OrderAttachmentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    client_name = serializers.CharField(source="client.name", read_only=True)
    cargo_type_name = serializers.CharField(
        source="cargo_type.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["order_number", "created_at", "updated_at"]
