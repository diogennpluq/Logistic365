"""DRF API Views for Routes app."""

from django.core.exceptions import ValidationError
from django.db.models import Max, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order

from .models import Route, Waypoint
from .serializers import (
    RouteCreateSerializer,
    RouteDetailSerializer,
    WaypointCreateSerializer,
    WaypointSerializer,
)


class RouteViewSet(viewsets.ModelViewSet):
    """
    CRUD маршрутов с кастомными actions.

    actions:
    - POST /routes/{id}/start/ — начать маршрут
    - POST /routes/{id}/complete/ — завершить маршрут
    - POST /routes/{id}/cancel/ — отменить маршрут
    - POST /routes/{id}/validate-load/ — проверить загрузку ТС
    - POST /routes/{id}/recalculate/ — пересчитать расстояние/время/топливо
    - POST /routes/{id}/add-order/{order_id}/ — добавить заказ в маршрут
    - POST /routes/{id}/remove-order/ — удалить заказ из маршрута
    - POST /routes/{id}/reorder-waypoints/ — переупорядочить точки
    - POST /routes/{id}/add-waypoint/ — добавить точку
    - POST /routes/{id}/auto-geocode/ — авто-расставить координаты (заглушка)
    """

    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        qs = Route.objects.select_related(
            "vehicle", "driver", "created_by"
        ).prefetch_related("orders", "waypoints")
        return qs

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RouteCreateSerializer
        return RouteDetailSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    # ─── Фильтрация ─────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()

        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        vehicle_filter = request.query_params.get("vehicle_id")
        if vehicle_filter:
            qs = qs.filter(vehicle_id=vehicle_filter)

        driver_filter = request.query_params.get("driver_id")
        if driver_filter:
            qs = qs.filter(driver_id=driver_filter)

        active_only = request.query_params.get("active_only")
        if active_only and active_only.lower() == "true":
            qs = qs.filter(is_active=True)

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search))

        ordering = request.query_params.get("ordering", "-created_at")
        qs = qs.order_by(ordering)

        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    # ─── Статусные actions ──────────────────────────────────────

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        """Начать выполнение маршрута."""
        route = self.get_object()
        try:
            route.start()
        except ValidationError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(route)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Завершить маршрут."""
        route = self.get_object()
        try:
            route.complete()
        except ValidationError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(route)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Отменить маршрут."""
        route = self.get_object()
        try:
            route.cancel()
        except ValidationError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(route)
        return Response(serializer.data)

    # ─── Расчёты ────────────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def recalculate(self, request, pk=None):
        """Пересчитать расстояние, время и расход топлива."""
        route = self.get_object()
        use_api = request.data.get("use_api", False)
        route.calculate_distance_and_time(use_api=use_api)
        serializer = self.get_serializer(route)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def validate_load(self, request, pk=None):
        """Проверить загрузку ТС по весу и объёму."""
        route = self.get_object()
        errors = route.validate_load()
        return Response(
            {
                "valid": len(errors) == 0,
                "errors": errors,
                "total_weight_kg": route.total_weight_kg,
                "total_volume_m3": route.total_volume_m3,
                "vehicle_capacity_kg": route.vehicle.capacity_kg if route.vehicle else None,
                "vehicle_volume_m3": route.vehicle.volume_m3 if route.vehicle else None,
                "load_percentage_weight": route.load_percentage_weight,
                "load_percentage_volume": route.load_percentage_volume,
            }
        )

    # ─── Работа с заказами ──────────────────────────────────────

    @action(detail=True, methods=["post"], url_path="add-order/(?P<order_id>[^/.]+)")
    def add_order(self, request, pk=None, order_id=None):
        """Добавить заказ в маршрут (создаёт точки погрузки/разгрузки)."""
        route = self.get_object()
        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return Response(
                {"error": "Заказ не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        if order in route.orders.all():
            return Response(
                {"error": "Заказ уже в маршруте"}, status=status.HTTP_400_BAD_REQUEST
            )

        route.add_waypoint_from_order(order)
        route.calculate_distance_and_time()
        serializer = self.get_serializer(route)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def remove_order(self, request, pk=None):
        """Удалить заказ из маршрута."""
        order_id = request.data.get("order_id")
        if not order_id:
            return Response(
                {"error": "order_id обязателен"}, status=status.HTTP_400_BAD_REQUEST
            )

        route = self.get_object()
        route.orders.filter(pk=order_id).remove()
        route.waypoints.filter(order_id=order_id).delete()

        # Перенумеровать оставшиеся точки
        for seq, wp in enumerate(route.waypoints.order_by("sequence"), start=1):
            wp.sequence = seq
            wp.save(update_fields=["sequence"])

        route.calculate_distance_and_time()
        serializer = self.get_serializer(route)
        return Response(serializer.data)

    # ─── Работа с точками ───────────────────────────────────────

    @action(detail=True, methods=["post"])
    def reorder_waypoints(self, request, pk=None):
        """
        Переупорядочить точки.
        body: {"ordered_ids": [3, 1, 5, 2, 4]}
        """
        route = self.get_object()
        ordered_ids = request.data.get("ordered_ids", [])
        if not ordered_ids:
            return Response(
                {"error": "ordered_ids обязателен"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        route.reorder_waypoints(ordered_ids)
        serializer = self.get_serializer(route)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_waypoint(self, request, pk=None):
        """Добавить точку в маршрут."""
        route = self.get_object()
        serializer = WaypointCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        max_seq = route.waypoints.aggregate(mx=Max("sequence"))["mx"] or 0
        serializer.save(route=route, sequence=max_seq + 1)

        route.calculate_distance_and_time()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def auto_geocode(self, request, pk=None):
        """Автоматически расставить координаты точкам без lat/lng (заглушка)."""
        route = self.get_object()
        route.auto_add_geocodes()
        route.calculate_distance_and_time()
        serializer = self.get_serializer(route)
        return Response(serializer.data)


class WaypointViewSet(viewsets.ModelViewSet):
    """CRUD точек маршрута."""

    permission_classes = [IsAuthenticated]
    serializer_class = WaypointSerializer
    lookup_field = "pk"

    def get_queryset(self):
        qs = Waypoint.objects.select_related("route", "order").order_by(
            "route", "sequence"
        )

        route_id = self.request.query_params.get("route_id")
        if route_id:
            qs = qs.filter(route_id=route_id)

        point_type = self.request.query_params.get("point_type")
        if point_type:
            qs = qs.filter(point_type=point_type)

        unvisited = self.request.query_params.get("unvisited")
        if unvisited and unvisited.lower() == "true":
            qs = qs.filter(visited=False)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(Q(address__icontains=search))

        return qs

    @action(detail=True, methods=["post"])
    def mark_visited(self, request, pk=None):
        """Отметить точку как посещённую."""
        wp = self.get_object()
        wp.visited = True
        wp.actual_arrival = timezone.now()
        wp.save(update_fields=["visited", "actual_arrival"])
        serializer = self.get_serializer(wp)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def move_up(self, request, pk=None):
        """Переместить точку выше (уменьшить sequence)."""
        wp = self.get_object()
        if wp.sequence <= 1:
            return Response({"detail": "Уже первая"})
        prev = Waypoint.objects.filter(
            route=wp.route, sequence=wp.sequence - 1
        ).first()
        if prev:
            prev.sequence, wp.sequence = wp.sequence, prev.sequence
            prev.save(update_fields=["sequence"])
            wp.save(update_fields=["sequence"])
        wp.route.calculate_distance_and_time()
        serializer = self.get_serializer(wp)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def move_down(self, request, pk=None):
        """Переместить точку ниже (увеличить sequence)."""
        wp = self.get_object()
        max_seq = Waypoint.objects.filter(route=wp.route).aggregate(
            mx=Max("sequence")
        )["mx"]
        if wp.sequence >= max_seq:
            return Response({"detail": "Уже последняя"})
        next_wp = Waypoint.objects.filter(
            route=wp.route, sequence=wp.sequence + 1
        ).first()
        if next_wp:
            next_wp.sequence, wp.sequence = wp.sequence, next_wp.sequence
            next_wp.save(update_fields=["sequence"])
            wp.save(update_fields=["sequence"])
        wp.route.calculate_distance_and_time()
        serializer = self.get_serializer(wp)
        return Response(serializer.data)
