"""DRF Serializers for Tracking app."""

from rest_framework import serializers

from .models import TrackingEvent, Waybill, WaybillAttachment


class TrackingEventSerializer(serializers.ModelSerializer):
    """Serializer for TrackingEvent model."""

    event_type_display = serializers.CharField(
        source="get_event_type_display", read_only=True
    )

    class Meta:
        model = TrackingEvent
        fields = "__all__"
        read_only_fields = ["timestamp"]


class WaybillAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for WaybillAttachment model."""

    doc_type_display = serializers.CharField(source="get_doc_type_display", read_only=True)

    class Meta:
        model = WaybillAttachment
        fields = "__all__"
        read_only_fields = ["uploaded_at"]


class WaybillSerializer(serializers.ModelSerializer):
    """Serializer for Waybill model with nested attachments."""

    attachments = WaybillAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Waybill
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
