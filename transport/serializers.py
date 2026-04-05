"""DRF Serializers for Transport app."""

from rest_framework import serializers

from .models import Vehicle, Driver, TripLog


class VehicleSerializer(serializers.ModelSerializer):
    """Serializer for Vehicle model."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    vehicle_type_display = serializers.CharField(
        source="get_vehicle_type_display", read_only=True
    )

    class Meta:
        model = Vehicle
        fields = "__all__"


class DriverSerializer(serializers.ModelSerializer):
    """Serializer for Driver model."""

    full_name = serializers.CharField(read_only=True)
    vehicle = VehicleSerializer(read_only=True)

    class Meta:
        model = Driver
        fields = "__all__"


class TripLogSerializer(serializers.ModelSerializer):
    """Serializer for TripLog model."""

    driver = DriverSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    driver_id = serializers.PrimaryKeyRelatedField(
        source="driver",
        queryset=Driver.objects.all(),
        write_only=True,
    )
    vehicle_id = serializers.PrimaryKeyRelatedField(
        source="vehicle",
        queryset=Vehicle.objects.all(),
        write_only=True,
    )

    class Meta:
        model = TripLog
        fields = "__all__"
