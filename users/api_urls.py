app_name = "api"
"""API URL routing for Users app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
