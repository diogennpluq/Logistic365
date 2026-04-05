"""Custom User model with roles for Logistic365."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    ADMIN = "admin", _("Администратор")
    DISPATCHER = "dispatcher", _("Диспетчер")
    DRIVER = "driver", _("Водитель")
    ACCOUNTANT = "accountant", _("Бухгалтер/Аналитик")


class User(AbstractUser):
    """Custom user model with role-based access."""

    role = models.CharField(
        _("Роль"),
        max_length=20,
        choices=Role.choices,
        default=Role.DISPATCHER,
    )
    phone = models.CharField(_("Телефон"), max_length=20, blank=True)
    avatar = models.ImageField(_("Аватар"), upload_to="avatars/", blank=True, null=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_dispatcher(self):
        return self.role == Role.DISPATCHER

    @property
    def is_driver(self):
        return self.role == Role.DRIVER

    @property
    def is_accountant(self):
        return self.role == Role.ACCOUNTANT
