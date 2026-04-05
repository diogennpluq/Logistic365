"""References app models — clients, cargo types, fuel norms."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
    """Client / counterparty."""

    name = models.CharField(_("Название организации"), max_length=255)
    inn = models.CharField(_("ИНН"), max_length=12, blank=True)
    legal_address = models.TextField(_("Юридический адрес"), blank=True)
    contact_person = models.CharField(_("Контактное лицо"), max_length=255, blank=True)
    contact_phone = models.CharField(_("Телефон"), max_length=20, blank=True)
    contact_email = models.EmailField(_("Email"), blank=True)
    contract_number = models.CharField(_("Номер договора"), max_length=50, blank=True)
    contract_date = models.DateField(_("Дата договора"), null=True, blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Клиент")
        verbose_name_plural = _("Клиенты")
        ordering = ["name"]

    def __str__(self):
        return self.name


class CargoType(models.Model):
    """Type of cargo."""

    name = models.CharField(_("Название"), max_length=100)
    hazard_class = models.IntegerField(
        _("Класс опасности"), default=0, help_text=_("0 — неопасный, 1-9 — классы опасности")
    )
    description = models.TextField(_("Описание"), blank=True)

    class Meta:
        verbose_name = _("Тип груза")
        verbose_name_plural = _("Типы грузов")

    def __str__(self):
        return f"{self.name} (класс {self.hazard_class})"


class FuelNorm(models.Model):
    """Fuel consumption norm per vehicle type."""

    vehicle_type = models.CharField(_("Тип ТС"), max_length=100)
    consumption_city = models.DecimalField(
        _("Расход город, л/100км"), max_digits=6, decimal_places=2
    )
    consumption_highway = models.DecimalField(
        _("Расход трасса, л/100км"), max_digits=6, decimal_places=2
    )
    consumption_winter = models.DecimalField(
        _("Зимняя надбавка, л/100км"), max_digits=6, decimal_places=2, default=0
    )
    valid_from = models.DateField(_("Действует с"))
    valid_to = models.DateField(_("Действует по"), null=True, blank=True)

    class Meta:
        verbose_name = _("Норматив топлива")
        verbose_name_plural = _("Нормативы топлива")

    def __str__(self):
        return f"{self.vehicle_type}: {self.consumption_city}л/100км"
