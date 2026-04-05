from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone
from django.utils.timezone import now

from orders.models import Order, OrderStatus
from transport.models import TripLog, Vehicle, VehicleStatus


@login_required
def dashboard(request):
    """Главная панель — ключевые метрики и графики."""
    today = now().date()

    # --- Метрики ---
    active_statuses = (
        OrderStatus.CONFIRMED,
        OrderStatus.ASSIGNED,
        OrderStatus.IN_TRANSIT,
        OrderStatus.LOADED,
        OrderStatus.UNLOADED,
    )
    active_orders_count = Order.objects.filter(status__in=active_statuses).count()

    # Задержанные доставки — required_delivery_datetime уже прошёл, а заказ не завершён
    delayed_deliveries = Order.objects.filter(
        required_delivery_datetime__lt=now(),
        status__in=(
            OrderStatus.CONFIRMED,
            OrderStatus.ASSIGNED,
            OrderStatus.IN_TRANSIT,
            OrderStatus.LOADED,
        ),
    ).count()

    # ТС на линии
    vehicles_on_line = Vehicle.objects.filter(status=VehicleStatus.ON_LINE).count()

    # Завершено сегодня
    completed_today = Order.objects.filter(
        status=OrderStatus.COMPLETED,
        updated_at__date=today,
    ).count()

    # --- Последние заказы ---
    recent_orders = (
        Order.objects.select_related("client", "vehicle", "created_by")
        .order_by("-created_at")[:10]
    )

    # --- Данные для графика утилизации ТС ---
    # Распределение ТС по статусам
    vehicle_status_qs = (
        Vehicle.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    vehicle_status_data = {row["status"]: row["count"] for row in vehicle_status_qs}

    # Добавим нули для отсутствующих статусов
    vehicle_status_labels = [label for label, _ in VehicleStatus.choices]
    vehicle_status_labels_display = [label_display for _, label_display in VehicleStatus.choices]
    vehicle_status_values = [vehicle_status_data.get(s, 0) for s in vehicle_status_labels]

    # Загруженность ТС по дням недели (за последние 7 дней)
    week_ago = today - timezone.timedelta(days=7)
    daily_utilization = (
        TripLog.objects.filter(
            departure_date__date__gte=week_ago,
        )
        .values("departure_date__date")
        .annotate(trips=Count("id"))
        .order_by("departure_date__date")
    )
    utilization_dates = [entry["departure_date__date"].strftime("%d.%m") for entry in daily_utilization]
    utilization_trips = [entry["trips"] for entry in daily_utilization]

    # Заказы по статусам
    orders_by_status = (
        Order.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    status_labels_display_map = dict(OrderStatus.choices)
    orders_status_labels = [
        status_labels_display_map.get(row["status"], row["status"])
        for row in orders_by_status
    ]
    orders_status_values = [row["count"] for row in orders_by_status]

    context = {
        "active_orders_count": active_orders_count,
        "delayed_deliveries": delayed_deliveries,
        "vehicles_on_line": vehicles_on_line,
        "completed_today": completed_today,
        "recent_orders": recent_orders,
        "vehicle_status_labels": vehicle_status_labels_display,
        "vehicle_status_values": vehicle_status_values,
        "utilization_dates": utilization_dates,
        "utilization_trips": utilization_trips,
        "orders_status_labels": orders_status_labels,
        "orders_status_values": orders_status_values,
    }

    return render(request, "core/dashboard.html", context)
