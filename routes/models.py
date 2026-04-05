"""Routes models — маршруты, точки, расчёт загрузки."""

import logging
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

# Средняя скорость по типу дороги, км/ч
AVG_SPEED_CITY = 30
AVG_SPEED_HIGHWAY = 70
AVG_SPEED_MIXED = 50


class RouteStatus(models.TextChoices):
    DRAFT = "draft", _("Черновик")
    PLANNED = "planned", _("Запланирован")
    IN_PROGRESS = "in_progress", _("В выполнении")
    COMPLETED = "completed", _("Завершён")
    CANCELLED = "cancelled", _("Отменён")


class Route(models.Model):
    """Маршрут — последовательность точек с расчётом параметров."""

    name = models.CharField(_("Название маршрута"), max_length=255)
    status = models.CharField(
        _("Статус"),
        max_length=20,
        choices=RouteStatus.choices,
        default=RouteStatus.DRAFT,
    )
    orders = models.ManyToManyField(
        "orders.Order",
        related_name="routes",
        verbose_name=_("Заказы"),
        blank=True,
    )
    vehicle = models.ForeignKey(
        "transport.Vehicle",
        on_delete=models.CASCADE,
        related_name="routes",
        verbose_name=_("Транспортное средство"),
    )
    driver = models.ForeignKey(
        "transport.Driver",
        on_delete=models.CASCADE,
        related_name="routes",
        verbose_name=_("Водитель"),
    )
    total_distance_km = models.DecimalField(
        _("Общее расстояние, км"), max_digits=10, decimal_places=2, default=0
    )
    estimated_time_hours = models.DecimalField(
        _("Расчётное время, ч"), max_digits=8, decimal_places=2, default=0
    )
    estimated_fuel_l = models.DecimalField(
        _("Расчётный расход топлива, л"), max_digits=8, decimal_places=2, default=0
    )
    departure_datetime = models.DateTimeField(
        _("Дата/время отправления"), null=True, blank=True
    )
    estimated_completion_datetime = models.DateTimeField(
        _("Расчётное время завершения"), null=True, blank=True
    )
    actual_distance_km = models.DecimalField(
        _("Фактическое расстояние, км"), max_digits=10, decimal_places=2, default=0
    )
    actual_fuel_l = models.DecimalField(
        _("Фактический расход топлива, л"), max_digits=8, decimal_places=2, default=0
    )
    completed_at = models.DateTimeField(
        _("Время завершения"), null=True, blank=True
    )
    notes = models.TextField(_("Примечания диспетчера"), blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_routes",
        verbose_name=_("Создал"),
    )
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Маршрут")
        verbose_name_plural = _("Маршруты")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_active"]),
            models.Index(fields=["vehicle", "status"]),
            models.Index(fields=["driver", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    # ─── Расчёт загрузки ────────────────────────────────────────

    @property
    def total_weight_kg(self):
        """Суммарный вес всех заказов в маршруте."""
        result = self.orders.aggregate(total=models.Sum("cargo_weight_kg"))
        return result["total"] or Decimal("0")

    @property
    def total_volume_m3(self):
        """Суммарный объём всех заказов в маршруте."""
        result = self.orders.aggregate(total=models.Sum("cargo_volume_m3"))
        return result["total"] or Decimal("0")

    @property
    def load_percentage_weight(self):
        """Процент загрузки по весу."""
        if self.vehicle and self.vehicle.capacity_kg > 0:
            return min(
                round(self.total_weight_kg / self.vehicle.capacity_kg * 100, 1), 100
            )
        return 0

    @property
    def load_percentage_volume(self):
        """Процент загрузки по объёму."""
        if self.vehicle and self.vehicle.volume_m3 > 0:
            return min(
                round(self.total_volume_m3 / self.vehicle.volume_m3 * 100, 1), 100
            )
        return 0

    def validate_load(self):
        """Проверка: не превышена ли грузоподъёмность/объём ТС."""
        errors = []
        if self.vehicle:
            if self.total_weight_kg > self.vehicle.capacity_kg:
                errors.append(
                    _(
                        f"Превышена грузоподъёмность: "
                        f"{self.total_weight_kg} / {self.vehicle.capacity_kg} кг"
                    )
                )
            if self.total_volume_m3 > self.vehicle.volume_m3:
                errors.append(
                    _(
                        f"Превышен объём: "
                        f"{self.total_volume_m3} / {self.vehicle.volume_m3} м³"
                    )
                )
        return errors

    # ─── Расчёт расстояния и времени ────────────────────────────

    def calculate_distance_and_time(self, use_api=False):
        """
        Рассчитать расстояние и время маршрута.

        Если use_api=True и есть координаты всех точек — используется
        упрощённая формула гаверсинусов (Haversine). Для production
        здесь должен быть вызов API Яндекс.Карт / OSRM.

        Если координат нет — использует заглушку на основе
        количества точек × среднее расстояние.
        """
        waypoints = self.waypoints.order_by("sequence")
        if waypoints.count() < 2:
            self.total_distance_km = 0
            self.estimated_time_hours = 0
            self._calculate_fuel()
            self.save(
                update_fields=[
                    "total_distance_km",
                    "estimated_time_hours",
                    "estimated_fuel_l",
                ]
            )
            return

        total_distance = Decimal("0")
        prev = None
        for wp in waypoints:
            if prev and prev.latitude and prev.longitude and wp.latitude and wp.longitude:
                dist = _haversine_km(
                    float(prev.latitude),
                    float(prev.longitude),
                    float(wp.latitude),
                    float(wp.longitude),
                )
                total_distance += dist
            prev = wp

        # Если нет координат — заглушка: ~80 км между точками
        if total_distance == 0:
            total_distance = Decimal(str(waypoints.count() - 1)) * Decimal("80")

        self.total_distance_km = round(total_distance, 2)

        # Время = расстояние / средняя скорость + 1 ч на точку (погрузка/разгрузка)
        avg_speed = Decimal(str(AVG_SPEED_MIXED))
        drive_hours = total_distance / avg_speed
        service_hours = Decimal(str(waypoints.count())) * Decimal("1")
        self.estimated_time_hours = round(drive_hours + service_hours, 2)

        # Расчётное время завершения
        if self.departure_datetime:
            self.estimated_completion_datetime = self.departure_datetime + timedelta(
                hours=float(self.estimated_time_hours)
            )

        self._calculate_fuel()
        self.save(
            update_fields=[
                "total_distance_km",
                "estimated_time_hours",
                "estimated_completion_datetime",
                "estimated_fuel_l",
            ]
        )

    def _calculate_fuel(self):
        """Пересчитать расход топлива по нормативу ТС."""
        if self.vehicle and self.vehicle.fuel_consumption > 0:
            self.estimated_fuel_l = round(
                self.total_distance_km * Decimal(str(self.vehicle.fuel_consumption))
                / Decimal("100"),
                2,
            )
        else:
            self.estimated_fuel_l = Decimal("0")

    def recalculate_fuel(self):
        """Публичный метод пересчёта топлива."""
        self._calculate_fuel()
        self.save(update_fields=["estimated_fuel_l"])

    # ─── Управление статусом ────────────────────────────────────

    def start(self):
        """Начать выполнение маршрута."""
        load_errors = self.validate_load()
        if load_errors:
            raise ValidationError(
                _("Нельзя начать маршрут: ") + "; ".join(load_errors)
            )
        if self.status not in (RouteStatus.DRAFT, RouteStatus.PLANNED):
            raise ValidationError(
                _("Нельзя начать маршрут со статусом: ") + self.get_status_display()
            )
        self.status = RouteStatus.IN_PROGRESS
        if not self.departure_datetime:
            self.departure_datetime = timezone.now()
        self.save(update_fields=["status", "departure_datetime", "updated_at"])

    def complete(self):
        """Завершить маршрут."""
        if self.status != RouteStatus.IN_PROGRESS:
            raise ValidationError(_("Можно завершить только активный маршрут"))
        self.status = RouteStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at", "updated_at"])

    def cancel(self):
        """Отменить маршрут."""
        if self.status == RouteStatus.COMPLETED:
            raise ValidationError(_("Нельзя отменить завершённый маршрут"))
        self.status = RouteStatus.CANCELLED
        self.is_active = False
        self.save(update_fields=["status", "is_active", "updated_at"])

    # ─── Работа с точками ───────────────────────────────────────

    @transaction.atomic
    def reorder_waypoints(self, ordered_ids):
        """
        Переупорядочить точки маршрута.

        ordered_ids: список ID точек в нужном порядке.
        """
        for seq, wp_id in enumerate(ordered_ids, start=1):
            self.waypoints.filter(pk=wp_id).update(sequence=seq)
        self.calculate_distance_and_time()

    @transaction.atomic
    def add_waypoint_from_order(self, order):
        """Добавить точки погрузки и разгрузки из заказа."""
        existing_seq = self.waypoints.aggregate(
            max_seq=models.Max("sequence")
        )["max_seq"] or 0

        if not self.waypoints.filter(order=order).exists():
            self.waypoints.create(
                order=order,
                point_type="loading",
                address=order.loading_address,
                sequence=existing_seq + 1,
                scheduled_arrival=order.loading_datetime,
                notes=f"Погрузка: {order.cargo_name}",
            )
            self.waypoints.create(
                order=order,
                point_type="unloading",
                address=order.unloading_address,
                sequence=existing_seq + 2,
                scheduled_arrival=order.required_delivery_datetime,
                notes=f"Разгрузка: {order.cargo_name}",
            )
            if order not in self.orders.all():
                self.orders.add(order)

    @transaction.atomic
    def auto_add_geocodes(self):
        """
        Заглушка: добавить случайные координаты точкам без lat/lng.

        В production здесь должен быть вызов геокодера
        (Яндекс.Карты Geocoder / Nominatim).
        """
        import random

        # Москва по умолчанию
        base_lat = Decimal("55.75")
        base_lon = Decimal("37.62")

        for wp in self.waypoints.filter(latitude__isnull=True).order_by("sequence"):
            wp.latitude = base_lat + Decimal(str(random.uniform(-0.5, 0.5)))
            wp.longitude = base_lon + Decimal(str(random.uniform(-0.5, 0.5)))
            wp.save(update_fields=["latitude", "longitude"])


# ─── Haversine formula ──────────────────────────────────────────

import math


def _haversine_km(lat1, lon1, lat2, lon2):
    """Расстояние между двумя точками по формуле Haversine, км."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return Decimal(str(round(R * c, 2)))


# ─── Waypoint ───────────────────────────────────────────────────


class Waypoint(models.Model):
    """Точка на маршруте."""

    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="waypoints", verbose_name=_("Маршрут")
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="waypoints",
        verbose_name=_("Заказ"),
    )
    point_type = models.CharField(
        _("Тип точки"),
        max_length=20,
        choices=[
            ("loading", "Погрузка"),
            ("unloading", "Разгрузка"),
            ("intermediate", "Промежуточная"),
        ],
        default="intermediate",
    )
    address = models.TextField(_("Адрес"))
    latitude = models.DecimalField(
        _("Широта"), max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        _("Долгота"), max_digits=10, decimal_places=7, null=True, blank=True
    )
    sequence = models.IntegerField(_("Порядковый номер"), default=0)
    scheduled_arrival = models.DateTimeField(
        _("Плановое время прибытия"), null=True, blank=True
    )
    actual_arrival = models.DateTimeField(
        _("Фактическое время прибытия"), null=True, blank=True
    )
    visited = models.BooleanField(_("Посещена"), default=False)
    notes = models.TextField(_("Примечания"), blank=True)

    class Meta:
        verbose_name = _("Точка маршрута")
        verbose_name_plural = _("Точки маршрута")
        ordering = ["route", "sequence"]
        unique_together = [("route", "sequence")]

    def __str__(self):
        return f"[{self.sequence}] {self.get_point_type_display()}: {self.address}"

    def distance_to(self, other):
        """Расстояние до другой точки (км)."""
        if self.latitude and self.longitude and other.latitude and other.longitude:
            return _haversine_km(
                float(self.latitude),
                float(self.longitude),
                float(other.latitude),
                float(other.longitude),
            )
        return None
