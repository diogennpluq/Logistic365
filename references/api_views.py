"""DRF API Views for References app."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Client, CargoType, FuelNorm
from .serializers import ClientSerializer, CargoTypeSerializer, FuelNormSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Client objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = ClientSerializer
    search_fields = ["name", "inn", "contact_person", "contact_email"]
    ordering_fields = ["name", "created_at", "is_active"]
    ordering = ["name"]

    def get_queryset(self):
        return Client.objects.all()


class CargoTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing CargoType objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = CargoTypeSerializer
    search_fields = ["name"]
    ordering_fields = ["name", "hazard_class"]
    ordering = ["name"]

    def get_queryset(self):
        return CargoType.objects.all()


class FuelNormViewSet(viewsets.ModelViewSet):
    """ViewSet for managing FuelNorm objects."""

    permission_classes = [IsAuthenticated]
    serializer_class = FuelNormSerializer
    search_fields = ["vehicle_type"]
    ordering_fields = ["vehicle_type", "valid_from"]
    ordering = ["-valid_from"]

    def get_queryset(self):
        return FuelNorm.objects.all()
