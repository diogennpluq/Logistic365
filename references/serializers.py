"""DRF Serializers for References app."""

from rest_framework import serializers

from .models import Client, CargoType, FuelNorm


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model."""

    class Meta:
        model = Client
        fields = "__all__"


class CargoTypeSerializer(serializers.ModelSerializer):
    """Serializer for CargoType model."""

    class Meta:
        model = CargoType
        fields = "__all__"


class FuelNormSerializer(serializers.ModelSerializer):
    """Serializer for FuelNorm model."""

    class Meta:
        model = FuelNorm
        fields = "__all__"
