"""DRF API Views for Transport app."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Vehicle, Driver, TripLog
from .serializers import VehicleSerializer, DriverSerializer, TripLogSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Vehicle objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = VehicleSerializer
    search_fields = ["plate_number", "brand", "model"]
    ordering_fields = ["plate_number", "brand", "status", "created_at"]
    ordering = ["plate_number"]

    def get_queryset(self):
        return Vehicle.objects.all()


class DriverViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Driver objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = DriverSerializer
    search_fields = ["last_name", "first_name", "patronymic", "phone", "license_number"]
    ordering_fields = ["last_name", "first_name", "is_active", "created_at"]
    ordering = ["last_name", "first_name"]

    def get_queryset(self):
        return Driver.objects.select_related("vehicle").all()


class TripLogViewSet(viewsets.ModelViewSet):
    """ViewSet for managing TripLog objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = TripLogSerializer
    search_fields = ["driver__last_name", "driver__first_name", "vehicle__plate_number"]
    ordering_fields = ["departure_date", "mileage", "fuel_consumed", "created_at"]
    ordering = ["-departure_date"]

    def get_queryset(self):
        return TripLog.objects.select_related("driver", "vehicle").all()
