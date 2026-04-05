app_name = "api"
"""API URL routing for References app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import ClientViewSet, CargoTypeViewSet, FuelNormViewSet

router = DefaultRouter()
router.register(r"clients", ClientViewSet, basename="client")
router.register(r"cargo-types", CargoTypeViewSet, basename="cargotype")
router.register(r"fuel-norms", FuelNormViewSet, basename="fuelnorm")

urlpatterns = [
    path("", include(router.urls)),
]
