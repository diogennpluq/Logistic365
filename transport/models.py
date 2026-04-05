"""Transport & Drivers models."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class VehicleStatus(models.TextChoices):
    OK = "ok", _("Исправен")
    REPAIR = "repair", _("В ремонте")
    ON_LINE = "on_line", _("На линии")
    WRITE_OFF = "write_off", _("Списан")


class VehicleType(models.TextChoices):
    VAN = "van", _("Фургон")
    REFRIGERATOR = "refrigerator", _("Рефрижератор")
    TANK = "tank", _("Цистерна")
    FLATBED = "flatbed", _("Бортовой")
    CONTAINER = "container", _("Контейнеровоз")
    OTHER = "other", _("Другое")


class Vehicle(models.Model):
    """Transport vehicle."""

    plate_number = models.CharField(_("Гос. номер"), max_length=20, unique=True)
    vehicle_type = models.CharField(
        _("Тип ТС"), max_length=20, choices=VehicleType.choices, default=VehicleType.VAN
    )
    brand = models.CharField(_("Марка"), max_length=100, blank=True)
    model = models.CharField(_("Модель"), max_length=100, blank=True)
    capacity_kg = models.DecimalField(_("Грузоподъёмность, кг"), max_digits=8, decimal_places=2)
    volume_m3 = models.DecimalField(_("Объём кузова, м³"), max_digits=8, decimal_places=2)
    current_mileage = models.IntegerField(_("Текущий пробег, км"), default=0)
    fuel_consumption = models.DecimalField(
        _("Расход топлива, л/100км"), max_digits=6, decimal_places=2, default=0
    )
    next_maintenance = models.DateField(_("Дата следующего ТО"), null=True, blank=True)
    status = models.CharField(
        _("Статус"), max_length=20, choices=VehicleStatus.choices, default=VehicleStatus.OK
    )
    notes = models.TextField(_("Примечания"), blank=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Транспортное средство")
        verbose_name_plural = _("Транспортные средства")
        ordering = ["plate_number"]

    def __str__(self):
        return f"{self.plate_number} ({self.get_vehicle_type_display()})"


class Driver(models.Model):
    """Driver."""

    last_name = models.CharField(_("Фамилия"), max_length=100)
    first_name = models.CharField(_("Имя"), max_length=100)
    patronymic = models.CharField(_("Отчество"), max_length=100, blank=True)
    phone = models.CharField(_("Телефон"), max_length=20, blank=True)
    license_number = models.CharField(_("Номер удостоверения"), max_length=50)
    license_category = models.CharField(
        _("Категория прав"), max_length=20, default="C"
    )
    medical_exam_date = models.DateField(_("Дата медосмотра"), null=True, blank=True)
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="drivers",
        verbose_name=_("Закреплённое ТС"),
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Водитель")
        verbose_name_plural = _("Водители")
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self):
        parts = [self.last_name, self.first_name, self.patronymic]
        return " ".join(p for p in parts if p)


class TripLog(models.Model):
    """Trip log entry — records after-trip data."""

    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="trip_logs", verbose_name=_("Водитель")
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="trip_logs", verbose_name=_("ТС")
    )
    departure_date = models.DateTimeField(_("Дата выезда"))
    arrival_date = models.DateTimeField(_("Дата возвращения"), null=True, blank=True)
    mileage = models.IntegerField(_("Пробег за рейс, км"), default=0)
    fuel_consumed = models.DecimalField(
        _("Расход топлива, л"), max_digits=8, decimal_places=2, default=0
    )
    notes = models.TextField(_("Примечания"), blank=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)

    class Meta:
        verbose_name = _("Журнал рейса")
        verbose_name_plural = _("Журнал рейсов")
        ordering = ["-departure_date"]

    def __str__(self):
        return f"{self.driver} — {self.vehicle.plate_number} — {self.department_date:%d.%m.%Y}"
