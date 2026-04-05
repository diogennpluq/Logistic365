app_name = "api"
"""API URL routing for Tracking app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import TrackingEventViewSet, WaybillViewSet

router = DefaultRouter()
router.register(r"tracking-events", TrackingEventViewSet, basename="trackingevent")
router.register(r"waybills", WaybillViewSet, basename="waybill")

urlpatterns = [
    path("", include(router.urls)),
]
