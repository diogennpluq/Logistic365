"""Orders views."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, ListView

from references.models import Client
from transport.models import Driver

from .models import Order, OrderStatus, OrderAttachment, OrderStatusLog


class OrderListView(LoginRequiredMixin, ListView):
    """Список заказов с фильтрацией и поиском."""

    model = Order
    template_name = "orders/order_list.html"
    context_object_name = "orders"
    paginate_by = 20

    def get_queryset(self):
        qs = Order.objects.select_related("client", "vehicle", "driver", "cargo_type", "created_by").order_by(
            "-created_at"
        )

        # Фильтр по статусу
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        # Фильтр по дате
        date_from = self.request.GET.get("date_from")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = self.request.GET.get("date_to")
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        # Фильтр по клиенту
        client_id = self.request.GET.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)

        # Фильтр по водителю
        driver_id = self.request.GET.get("driver")
        if driver_id:
            qs = qs.filter(driver_id=driver_id)

        # Поиск
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(order_number__icontains=query)
                | Q(cargo_name__icontains=query)
                | Q(client__name__icontains=query)
                | Q(loading_address__icontains=query)
                | Q(unloading_address__icontains=query)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = OrderStatus.choices
        context["clients"] = Client.objects.filter(is_active=True).order_by("name")
        context["drivers"] = Driver.objects.filter(is_active=True).order_by("last_name", "first_name")

        # Сохраняем текущие фильтры
        context["current_status"] = self.request.GET.get("status", "")
        context["current_date_from"] = self.request.GET.get("date_from", "")
        context["current_date_to"] = self.request.GET.get("date_to", "")
        context["current_client"] = self.request.GET.get("client", "")
        context["current_driver"] = self.request.GET.get("driver", "")
        context["current_query"] = self.request.GET.get("q", "")

        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о заказе."""

    model = Order
    template_name = "orders/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.select_related(
            "client", "vehicle", "driver", "cargo_type", "created_by"
        ).prefetch_related("status_logs", "tracking_events", "attachments")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_logs"] = self.object.status_logs.all()[:20]
        context["tracking_events"] = self.object.tracking_events.all()[:20]
        context["attachments"] = self.object.attachments.all()
        context["statuses"] = OrderStatus.choices
        return context


@login_required
def change_order_status(request, pk):
    """Изменение статуса заказа."""
    order = get_object_or_404(Order, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        comment = request.POST.get("comment", "")
        if new_status and new_status in dict(OrderStatus.choices):
            old_status = order.status
            order.status = new_status
            order.save(update_fields=["status", "updated_at"])

            OrderStatusLog.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status,
                comment=comment,
                changed_by=request.user,
            )
    return redirect("orders:detail", pk=order.pk)
