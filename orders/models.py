"""Orders models."""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from references.models import Client, CargoType


class OrderStatus(models.TextChoices):
    DRAFT = "draft", _("Черновик")
    CONFIRMED = "confirmed", _("Подтверждён")
    ASSIGNED = "assigned", _("Назначен на рейс")
    IN_TRANSIT = "in_transit", _("В пути")
    LOADED = "loaded", _("Загружен")
    UNLOADED = "unloaded", _("Выгружен")
    COMPLETED = "completed", _("Завершён")
    CANCELLED = "cancelled", _("Отменён")


class Order(models.Model):
    """Shipping order."""

    order_number = models.CharField(
        _("Номер заказа"), max_length=50, unique=True, editable=False
    )
    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name="orders", verbose_name=_("Клиент")
    )
    cargo_name = models.CharField(_("Наименование груза"), max_length=255)
    cargo_type = models.ForeignKey(
        CargoType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Тип груза"),
    )
    cargo_weight_kg = models.DecimalField(_("Вес, кг"), max_digits=10, decimal_places=2)
    cargo_volume_m3 = models.DecimalField(_("Объём, м³"), max_digits=10, decimal_places=2)
    hazard_class = models.IntegerField(_("Класс опасности"), default=0)
    loading_address = models.TextField(_("Адрес погрузки"))
    unloading_address = models.TextField(_("Адрес разгрузки"))
    loading_datetime = models.DateTimeField(_("Дата/время загрузки"))
    required_delivery_datetime = models.DateTimeField(_("Требуемая дата доставки"))
    special_conditions = models.TextField(_("Особые условия"), blank=True)
    status = models.CharField(
        _("Статус"), max_length=20, choices=OrderStatus.choices, default=OrderStatus.DRAFT
    )
    vehicle = models.ForeignKey(
        "transport.Vehicle",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Транспортное средство"),
    )
    driver = models.ForeignKey(
        "transport.Driver",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("Водитель"),
    )
    documents = models.FileField(
        _("Документы"), upload_to="order_docs/", blank=True, null=True
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_orders",
        verbose_name=_("Создан пользователем"),
    )
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Заказ")
        verbose_name_plural = _("Заказы")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Заказ {self.order_number} — {self.cargo_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            date_str = timezone.now().strftime("%Y%m%d")
            unique_id = uuid.uuid4().hex[:6].upper()
            self.order_number = f"ORD-{date_str}-{unique_id}"
        super().save(*args, **kwargs)


class OrderStatusLog(models.Model):
    """Log of order status changes."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="status_logs", verbose_name=_("Заказ")
    )
    old_status = models.CharField(_("Старый статус"), max_length=20)
    new_status = models.CharField(_("Новый статус"), max_length=20)
    comment = models.TextField(_("Комментарий"), blank=True)
    changed_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Изменил"),
    )
    changed_at = models.DateTimeField(_("Дата изменения"), auto_now_add=True)

    class Meta:
        verbose_name = _("Лог статуса заказа")
        verbose_name_plural = _("Логи статусов заказов")
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"


class OrderAttachment(models.Model):
    """Attached files for order (invoices, photos)."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="attachments", verbose_name=_("Заказ")
    )
    file = models.FileField(_("Файл"), upload_to="order_attachments/")
    description = models.CharField(_("Описание"), max_length=255, blank=True)
    uploaded_at = models.DateTimeField(_("Загружен"), auto_now_add=True)

    class Meta:
        verbose_name = _("Вложение заказа")
        verbose_name_plural = _("Вложения заказов")

    def __str__(self):
        return f"Вложение к {self.order.order_number}"
