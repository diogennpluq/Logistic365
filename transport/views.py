"""Transport views."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Vehicle, Driver


class VehicleListView(LoginRequiredMixin, ListView):
    """Список транспортных средств."""

    model = Vehicle
    template_name = "transport/vehicle_list.html"
    context_object_name = "vehicles"
    paginate_by = 20

    def get_queryset(self):
        qs = Vehicle.objects.all().order_by("plate_number")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Vehicle.status.field.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class DriverListView(LoginRequiredMixin, ListView):
    """Список водителей."""

    model = Driver
    template_name = "transport/driver_list.html"
    context_object_name = "drivers"
    paginate_by = 20

    def get_queryset(self):
        qs = Driver.objects.select_related("vehicle").order_by("last_name", "first_name")
        is_active = self.request.GET.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "1")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_active"] = self.request.GET.get("is_active", "")
        return context
