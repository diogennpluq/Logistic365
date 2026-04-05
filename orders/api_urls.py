app_name = "api"
"""API URL routing for Orders app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import OrderViewSet, OrderStatusLogViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-status-logs", OrderStatusLogViewSet, basename="orderstatuslog")

urlpatterns = [
    path("", include(router.urls)),
]
