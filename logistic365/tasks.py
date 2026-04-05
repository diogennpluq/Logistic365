"""Celery tasks for Logistic365."""

import logging
from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q

from celery import shared_task

from orders.models import Order, OrderStatus
from transport.models import Vehicle
from references.models import Client

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_notification(self, order_id: int, subject: str, message: str):
    """Send email notification about order status change."""
    try:
        send_mail(
            subject=f"[Логистика 365] {subject}",
            message=message,
            from_email=None,  # Use DEFAULT_FROM_EMAIL
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception(f"Failed to send notification for order {order_id}")
        raise self.retry(exc=exc, countdown=60 * 5)


@shared_task
def generate_daily_report():
    """Generate daily summary report and log it."""
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today).count()
    completed_today = Order.objects.filter(
        updated_at__date=today, status=OrderStatus.COMPLETED
    ).count()
    delayed = Order.objects.filter(
        status__in=[OrderStatus.IN_TRANSIT, OrderStatus.ASSIGNED],
        required_delivery_datetime__lt=timezone.now(),
    ).count()
    vehicles_on_line = Vehicle.objects.filter(status=VehicleStatus.ON_LINE).count()

    report = (
        f"Ежедневный отчёт за {today}:\n"
        f"- Создано заказов: {orders_today}\n"
        f"- Завершено: {completed_today}\n"
        f"- Задержанных: {delayed}\n"
        f"- ТС на линии: {vehicles_on_line}"
    )
    logger.info(report)
    return report


@shared_task
def check_delayed_orders():
    """Find delayed orders and log warnings."""
    delayed = Order.objects.filter(
        status__in=[OrderStatus.IN_TRANSIT, OrderStatus.ASSIGNED, OrderStatus.LOADED],
        required_delivery_datetime__lt=timezone.now(),
    ).select_related("client", "driver", "vehicle")

    for order in delayed:
        logger.warning(
            f"Задержанный заказ: {order.order_number} — "
            f"Клиент: {order.client}, "
            f"Водитель: {order.driver}, "
            f"Требуемая доставка: {order.required_delivery_datetime}"
        )

    return f"Проверено, задержанных: {delayed.count()}"


@shared_task
def calculate_route_statistics():
    """Calculate and log route statistics for the past week."""
    from routes.models import Route

    week_ago = timezone.now() - timedelta(days=7)
    routes = Route.objects.filter(created_at__gte=week_ago)
    total_distance = sum(r.total_distance_km for r in routes)
    total_fuel = sum(r.estimated_fuel_l for r in routes)

    stats = (
        f"Статистика за неделю:\n"
        f"- Маршрутов: {routes.count()}\n"
        f"- Общее расстояние: {total_distance} км\n"
        f"- Расход топлива: {total_fuel} л"
    )
    logger.info(stats)
    return stats


@shared_task
def send_telegram_alert(message: str):
    """Send alert to Telegram chat if configured."""
    import requests

    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)

    if not token or not chat_id:
        logger.debug("Telegram not configured, skipping alert")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(
            url,
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
    except Exception as exc:
        logger.exception("Failed to send Telegram alert")
        raise
