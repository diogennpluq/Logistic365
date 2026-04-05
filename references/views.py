"""Web views for References app — клиенты, типы грузов, нормативы топлива."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from orders.models import Order

from .models import CargoType, Client, FuelNorm


# ─── Клиенты ─────────────────────────────────────────────────────


class ClientListView(LoginRequiredMixin, ListView):
    """Список клиентов с фильтрацией и поиском."""

    model = Client
    template_name = "references/client_list.html"
    context_object_name = "clients"
    paginate_by = 25

    def get_queryset(self):
        qs = Client.objects.annotate(orders_count=Count("orders"))

        # Фильтр по активности
        active = self.request.GET.get("active")
        if active == "true":
            qs = qs.filter(is_active=True)
        elif active == "false":
            qs = qs.filter(is_active=False)

        # Поиск
        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(inn__icontains=search)
                | Q(contact_person__icontains=search)
                | Q(contact_email__icontains=search)
            )

        ordering = self.request.GET.get("ordering", "name")
        return qs.order_by(ordering)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_search"] = self.request.GET.get("q", "")
        ctx["current_active"] = self.request.GET.get("active", "")
        return ctx


class ClientDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница клиента."""

    model = Client
    template_name = "references/client_detail.html"
    context_object_name = "client"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["orders"] = (
            Order.objects.filter(client=self.object)
            .select_related("vehicle", "driver")
            .order_by("-created_at")[:50]
        )
        return ctx


class ClientCreateView(LoginRequiredMixin, CreateView):
    """Создание клиента."""

    model = Client
    template_name = "references/client_form.html"
    fields = [
        "name",
        "inn",
        "legal_address",
        "contact_person",
        "contact_phone",
        "contact_email",
        "contract_number",
        "contract_date",
        "is_active",
    ]
    success_url = reverse_lazy("references:client_list")


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование клиента."""

    model = Client
    template_name = "references/client_form.html"
    fields = [
        "name",
        "inn",
        "legal_address",
        "contact_person",
        "contact_phone",
        "contact_email",
        "contract_number",
        "contract_date",
        "is_active",
    ]
    success_url = reverse_lazy("references:client_list")


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление клиента."""

    model = Client
    template_name = "references/client_confirm_delete.html"
    success_url = reverse_lazy("references:client_list")


# ─── Типы грузов ─────────────────────────────────────────────────


class CargoTypeListView(LoginRequiredMixin, ListView):
    """Список типов грузов."""

    model = CargoType
    template_name = "references/cargotype_list.html"
    context_object_name = "cargo_types"

    def get_queryset(self):
        qs = CargoType.objects.annotate(orders_count=Count("orders"))

        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(Q(name__icontains=search))

        hazard = self.request.GET.get("hazard_class")
        if hazard:
            qs = qs.filter(hazard_class=hazard)

        return qs.order_by("hazard_class", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_search"] = self.request.GET.get("q", "")
        ctx["current_hazard"] = self.request.GET.get("hazard_class", "")
        return ctx


class CargoTypeCreateView(LoginRequiredMixin, CreateView):
    """Создание типа груза."""

    model = CargoType
    template_name = "references/cargotype_form.html"
    fields = ["name", "hazard_class", "description"]
    success_url = reverse_lazy("references:cargotype_list")


class CargoTypeUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование типа груза."""

    model = CargoType
    template_name = "references/cargotype_form.html"
    fields = ["name", "hazard_class", "description"]
    success_url = reverse_lazy("references:cargotype_list")


class CargoTypeDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление типа груза."""

    model = CargoType
    template_name = "references/cargotype_confirm_delete.html"
    success_url = reverse_lazy("references:cargotype_list")


# ─── Нормативы топлива ───────────────────────────────────────────


class FuelNormListView(LoginRequiredMixin, ListView):
    """Список нормативов топлива."""

    model = FuelNorm
    template_name = "references/fuelnorm_list.html"
    context_object_name = "fuel_norms"

    def get_queryset(self):
        qs = FuelNorm.objects.all()

        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(Q(vehicle_type__icontains=search))

        return qs.order_by("-valid_from", "vehicle_type")

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        ctx = super().get_context_data(**kwargs)
        ctx["current_search"] = self.request.GET.get("q", "")
        ctx["today"] = timezone.now().date()
        return ctx


class FuelNormCreateView(LoginRequiredMixin, CreateView):
    """Создание норматива топлива."""

    model = FuelNorm
    template_name = "references/fuelnorm_form.html"
    fields = [
        "vehicle_type",
        "consumption_city",
        "consumption_highway",
        "consumption_winter",
        "valid_from",
        "valid_to",
    ]
    success_url = reverse_lazy("references:fuelnorm_list")


class FuelNormUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование норматива топлива."""

    model = FuelNorm
    template_name = "references/fuelnorm_form.html"
    fields = [
        "vehicle_type",
        "consumption_city",
        "consumption_highway",
        "consumption_winter",
        "valid_from",
        "valid_to",
    ]
    success_url = reverse_lazy("references:fuelnorm_list")


class FuelNormDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление норматива топлива."""

    model = FuelNorm
    template_name = "references/fuelnorm_confirm_delete.html"
    success_url = reverse_lazy("references:fuelnorm_list")


# ─── Главная страница справочников ───────────────────────────────


def references_index(request):
    """Главная страница справочников — карточки разделов."""
    from django.shortcuts import render

    ctx = {
        "clients_count": Client.objects.count(),
        "clients_active": Client.objects.filter(is_active=True).count(),
        "cargotypes_count": CargoType.objects.count(),
        "fuelnorms_count": FuelNorm.objects.count(),
    }
    return render(request, "references/index.html", ctx)
