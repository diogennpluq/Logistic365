"""DRF API Views for Tracking app."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import TrackingEvent, Waybill
from .serializers import TrackingEventSerializer, WaybillSerializer


class TrackingEventViewSet(viewsets.ModelViewSet):
    """ViewSet for managing TrackingEvent objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = TrackingEventSerializer
    search_fields = ["order__order_number", "event_type", "comment"]
    ordering_fields = ["timestamp", "event_type"]
    ordering = ["-timestamp"]

    def get_queryset(self):
        return TrackingEvent.objects.select_related("order", "recorded_by").all()


class WaybillViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Waybill objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = WaybillSerializer
    search_fields = ["number", "route_description"]
    ordering_fields = ["number", "issue_date", "is_closed", "created_at"]
    ordering = ["-issue_date"]

    def get_queryset(self):
        return (
            Waybill.objects.select_related("order", "driver", "vehicle")
            .prefetch_related("attachments")
            .all()
        )
