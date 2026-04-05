"""Tracking models — events, waybills, documents."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class EventType(models.TextChoices):
    ARRIVED_LOADING = "arrived_loading", _("Прибытие на погрузку")
    LOADING_START = "loading_start", _("Начало погрузки")
    LOADING_END = "loading_end", _("Завершение погрузки")
    DEPARTED = "departed", _("Выезд")
    ARRIVED_UNLOADING = "arrived_unloading", _("Прибытие на разгрузку")
    UNLOADING_START = "unloading_start", _("Начало разгрузки")
    UNLOADING_END = "unloading_end", _("Завершение разгрузки")
    COMPLETED = "completed", _("Завершение")
    DELAY = "delay", _("Задержка")
    CUSTOM = "custom", _("Другое")


class TrackingEvent(models.Model):
    """Event recorded during trip execution."""

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="tracking_events",
        verbose_name=_("Заказ"),
    )
    event_type = models.CharField(
        _("Тип события"), max_length=30, choices=EventType.choices
    )
    timestamp = models.DateTimeField(_("Время события"), auto_now_add=True)
    latitude = models.DecimalField(
        _("Широта"), max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        _("Долгота"), max_digits=10, decimal_places=7, null=True, blank=True
    )
    comment = models.TextField(_("Комментарий"), blank=True)
    recorded_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Записал"),
    )

    class Meta:
        verbose_name = _("Событие отслеживания")
        verbose_name_plural = _("События отслеживания")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.order.order_number} — {self.get_event_type_display()}"


class Waybill(models.Model):
    """Electronic waybill (путевой лист)."""

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="waybills",
        verbose_name=_("Заказ"),
    )
    number = models.CharField(_("Номер путевого листа"), max_length=50, unique=True)
    issue_date = models.DateField(_("Дата выдачи"))
    valid_until = models.DateField(_("Действителен до"))
    driver = models.ForeignKey(
        "transport.Driver",
        on_delete=models.CASCADE,
        related_name="waybills",
        verbose_name=_("Водитель"),
    )
    vehicle = models.ForeignKey(
        "transport.Vehicle",
        on_delete=models.CASCADE,
        related_name="waybills",
        verbose_name=_("ТС"),
    )
    route_description = models.TextField(_("Описание маршрута"), blank=True)
    fuel_issued = models.DecimalField(
        _("Топливо выдано, л"), max_digits=8, decimal_places=2, default=0
    )
    fuel_returned = models.DecimalField(
        _("Топливо сдано, л"), max_digits=8, decimal_places=2, default=0
    )
    mileage_start = models.IntegerField(_("Пробег при выезде, км"), default=0)
    mileage_end = models.IntegerField(_("Пробег при возвращении, км"), default=0)
    is_closed = models.BooleanField(_("Закрыт"), default=False)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Путевой лист")
        verbose_name_plural = _("Путевые листы")
        ordering = ["-issue_date"]

    def __str__(self):
        return f"Путевой лист {self.number}"


class WaybillAttachment(models.Model):
    """Attached documents for waybill (TTN, acts)."""

    waybill = models.ForeignKey(
        Waybill,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Путевой лист"),
    )
    file = models.FileField(_("Файл"), upload_to="waybill_docs/")
    doc_type = models.CharField(
        _("Тип документа"),
        max_length=30,
        choices=[
            ("ttn", "ТТН"),
            ("act", "Акт"),
            ("photo", "Фото"),
            ("other", "Другое"),
        ],
        default="other",
    )
    uploaded_at = models.DateTimeField(_("Загружен"), auto_now_add=True)

    class Meta:
        verbose_name = _("Документ путевого листа")
        verbose_name_plural = _("Документы путевого листа")

    def __str__(self):
        return f"{self.get_doc_type_display()} к {self.waybill.number}"
