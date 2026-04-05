"""DRF API Views for Orders app."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, OrderStatus, OrderStatusLog
from .serializers import OrderSerializer, OrderStatusLogSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Order objects.

    Custom actions:
        change-status — POST /api/orders/{id}/change-status/
    """

    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer
    search_fields = ["order_number", "cargo_name", "client__name"]
    ordering_fields = ["order_number", "created_at", "loading_datetime", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Order.objects.select_related("client", "cargo_type", "vehicle", "driver", "created_by")
            .prefetch_related("status_logs", "attachments")
            .all()
        )

    @action(detail=True, methods=["post"], url_path="change-status")
    def change_status(self, request, pk=None):
        """Change order status and create a status log entry."""
        order = self.get_object()
        new_status = request.data.get("new_status")
        comment = request.data.get("comment", "")

        if not new_status:
            return Response(
                {"error": "Поле 'new_status' обязательно."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = [choice[0] for choice in OrderStatus.choices]
        if new_status not in valid_statuses:
            return Response(
                {"error": f"Недопустимый статус. Допустимые: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = order.status
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])

        OrderStatusLog.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            comment=comment,
            changed_by=request.user,
        )

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderStatusLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for reading OrderStatusLog objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderStatusLogSerializer
    ordering_fields = ["changed_at", "old_status", "new_status"]
    ordering = ["-changed_at"]

    def get_queryset(self):
        return OrderStatusLog.objects.select_related("order", "changed_by").all()
