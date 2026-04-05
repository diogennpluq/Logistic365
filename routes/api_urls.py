app_name = "api"
"""API URL routing for Routes app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import RouteViewSet, WaypointViewSet

router = DefaultRouter()
router.register(r"routes", RouteViewSet, basename="route")
router.register(r"waypoints", WaypointViewSet, basename="waypoint")

urlpatterns = [
    path("", include(router.urls)),
]
