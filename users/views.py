"""Users views."""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import ListView

from .models import User, Role


class CustomLoginView(LoginView):
    """Страница входа в систему."""
    template_name = "users/login.html"
    redirect_authenticated_user = True


class UserListView(UserPassesTestMixin, ListView):
    """Список пользователей (только для администраторов)."""

    model = User
    template_name = "users/user_list.html"
    context_object_name = "users"
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

    def get_login_url(self):
        return reverse_lazy("users:login")

    def get_queryset(self):
        qs = User.objects.all().order_by("-created_at")
        role = self.request.GET.get("role")
        if role:
            qs = qs.filter(role=role)
        is_active = self.request.GET.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active == "1")
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roles"] = Role.choices
        context["current_role"] = self.request.GET.get("role", "")
        context["current_active"] = self.request.GET.get("is_active", "")
        return context
