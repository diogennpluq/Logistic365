app_name = "api"
"""API URL routing for Transport app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import VehicleViewSet, DriverViewSet, TripLogViewSet

router = DefaultRouter()
router.register(r"vehicles", VehicleViewSet, basename="vehicle")
router.register(r"drivers", DriverViewSet, basename="driver")
router.register(r"trip-logs", TripLogViewSet, basename="triplog")

urlpatterns = [
    path("", include(router.urls)),
]
