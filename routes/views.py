"""Web views for Routes app."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from orders.models import Order
from transport.models import Driver, Vehicle

from .models import Route, RouteStatus, Waypoint


class RouteListView(LoginRequiredMixin, ListView):
    """Список маршрутов с фильтрацией."""

    model = Route
    template_name = "routes/route_list.html"
    context_object_name = "routes"
    paginate_by = 20

    def get_queryset(self):
        qs = Route.objects.select_related(
            "vehicle", "driver", "created_by"
        ).prefetch_related("orders").annotate(
            waypoints_count=Count("waypoints"),
            orders_count=Count("orders", distinct=True),
        )

        # Фильтр по статусу
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        # Фильтр по ТС
        vehicle_id = self.request.GET.get("vehicle_id")
        if vehicle_id:
            qs = qs.filter(vehicle_id=vehicle_id)

        # Фильтр по водителю
        driver_id = self.request.GET.get("driver_id")
        if driver_id:
            qs = qs.filter(driver_id=driver_id)

        # Только активные
        if self.request.GET.get("active_only") == "true":
            qs = qs.filter(is_active=True)

        # Поиск
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(driver__last_name__icontains=search)
                | Q(vehicle__plate_number__icontains=search)
            )

        ordering = self.request.GET.get("ordering", "-created_at")
        return qs.order_by(ordering)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = RouteStatus.choices
        ctx["vehicles"] = Vehicle.objects.exclude(status="write_off")[:50]
        ctx["drivers"] = Driver.objects.filter(is_active=True)[:50]
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_vehicle"] = self.request.GET.get("vehicle_id", "")
        ctx["current_driver"] = self.request.GET.get("driver_id", "")
        ctx["current_search"] = self.request.GET.get("q", "")
        return ctx


class RouteDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница маршрута."""

    model = Route
    template_name = "routes/route_detail.html"
    context_object_name = "route"

    def get_object(self, queryset=None):
        return Route.objects.select_related(
            "vehicle", "driver", "created_by"
        ).prefetch_related(
            "orders",
            "waypoints__order",
        ).get(pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        route = self.object

        ctx["waypoints"] = route.waypoints.select_related("order").order_by("sequence")
        ctx["orders"] = route.orders.all()
        ctx["available_orders"] = Order.objects.exclude(
            routes=route
        ).filter(status__in=["confirmed", "assigned"])[:50]
        ctx["load_errors"] = route.validate_load()
        return ctx


class RouteCreateView(LoginRequiredMixin, CreateView):
    """Создание маршрута."""

    model = Route
    template_name = "routes/route_form.html"
    fields = ["name", "vehicle", "driver", "departure_datetime", "notes"]
    success_url = reverse_lazy("routes:list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Новый маршрут"
        ctx["orders"] = Order.objects.filter(
            status__in=["confirmed", "assigned"]
        ).select_related("client")[:100]
        ctx["vehicles"] = Vehicle.objects.filter(
            status__in=["ok", "on_line"]
        )[:50]
        ctx["drivers"] = Driver.objects.filter(is_active=True)[:50]
        return ctx


class RouteUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование маршрута."""

    model = Route
    template_name = "routes/route_form.html"
    fields = ["name", "vehicle", "driver", "departure_datetime", "notes"]
    success_url = reverse_lazy("routes:list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Редактировать: {self.object.name}"
        return ctx


@login_required
def route_calculate(request, pk):
    """Пересчитать расстояние/время/топливо маршрута."""
    route = get_object_or_404(Route, pk=pk)
    route.calculate_distance_and_time()
    return redirect("routes:detail", pk=pk)


@login_required
def route_start(request, pk):
    """Начать маршрут."""
    route = get_object_or_404(Route, pk=pk)
    try:
        route.start()
    except Exception:
        pass
    return redirect("routes:detail", pk=pk)


@login_required
def route_complete(request, pk):
    """Завершить маршрут."""
    route = get_object_or_404(Route, pk=pk)
    try:
        route.complete()
    except Exception:
        pass
    return redirect("routes:detail", pk=pk)


@login_required
def route_cancel(request, pk):
    """Отменить маршрут."""
    route = get_object_or_404(Route, pk=pk)
    try:
        route.cancel()
    except Exception:
        pass
    return redirect("routes:detail", pk=pk)


@login_required
def route_add_order(request, pk, order_id):
    """Добавить заказ в маршрут."""
    route = get_object_or_404(Route, pk=pk)
    order = get_object_or_404(Order, pk=order_id)
    route.add_waypoint_from_order(order)
    route.calculate_distance_and_time()
    return redirect("routes:detail", pk=pk)


@login_required
def route_remove_order(request, pk, order_id):
    """Удалить заказ из маршрута."""
    route = get_object_or_404(Route, pk=pk)
    route.orders.filter(pk=order_id).remove()
    route.waypoints.filter(order_id=order_id).delete()

    # Перенумеровать
    for seq, wp in enumerate(route.waypoints.order_by("sequence"), start=1):
        wp.sequence = seq
        wp.save(update_fields=["sequence"])

    route.calculate_distance_and_time()
    return redirect("routes:detail", pk=pk)


@login_required
def route_map(request, pk):
    """Карта маршрута с визуализацией точек."""
    route = get_object_or_404(
        Route.objects.prefetch_related("waypoints__order"), pk=pk
    )
    waypoints = route.waypoints.select_related("order").order_by("sequence")

    # Собрать данные для Leaflet
    points_data = []
    for wp in waypoints:
        points_data.append({
            "id": wp.pk,
            "lat": float(wp.latitude) if wp.latitude else None,
            "lng": float(wp.longitude) if wp.longitude else None,
            "type": wp.point_type,
            "type_display": wp.get_point_type_display(),
            "address": wp.address,
            "sequence": wp.sequence,
            "visited": wp.visited,
            "order_number": wp.order.order_number if wp.order else None,
            "notes": wp.notes,
        })

    return render(
        request,
        "routes/route_map.html",
        {
            "route": route,
            "waypoints": points_data,
            "has_coords": any(p["lat"] for p in points_data),
        },
    )


@login_required
def route_geocode(request, pk):
    """Авто-расставить координаты (заглушка)."""
    route = get_object_or_404(Route, pk=pk)
    route.auto_add_geocodes()
    route.calculate_distance_and_time()
    return redirect("routes:map", pk=pk)
