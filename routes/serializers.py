"""DRF Serializers for Routes app — с вложенным созданием/редактированием точек."""

from rest_framework import serializers

from .models import Route, Waypoint


class WaypointCreateSerializer(serializers.ModelSerializer):
    """Serializer для создания отдельной точки."""

    class Meta:
        model = Waypoint
        fields = [
            "id",
            "order",
            "point_type",
            "address",
            "latitude",
            "longitude",
            "sequence",
            "scheduled_arrival",
            "notes",
        ]

    def validate(self, attrs):
        if attrs.get("latitude") is not None and not (-90 <= attrs["latitude"] <= 90):
            raise serializers.ValidationError({"latitude": "Должна быть от -90 до 90"})
        if attrs.get("longitude") is not None and not (-180 <= attrs["longitude"] <= 180):
            raise serializers.ValidationError({"longitude": "Должна быть от -180 до 180"})
        return attrs


class WaypointSerializer(serializers.ModelSerializer):
    """Serializer для Waypoint — с read-only display полями."""

    point_type_display = serializers.CharField(
        source="get_point_type_display", read_only=True
    )
    order_number = serializers.CharField(
        source="order.order_number", read_only=True, allow_null=True
    )
    distance_from_prev_km = serializers.SerializerMethodField()

    class Meta:
        model = Waypoint
        fields = [
            "id",
            "route",
            "order",
            "order_number",
            "point_type",
            "point_type_display",
            "address",
            "latitude",
            "longitude",
            "sequence",
            "scheduled_arrival",
            "actual_arrival",
            "visited",
            "notes",
            "distance_from_prev_km",
        ]
        read_only_fields = ["distance_from_prev_km"]

    def get_distance_from_prev_km(self, obj):
        """Расстояние от предыдущей точки."""
        prev = (
            Waypoint.objects.filter(route=obj.route, sequence__lt=obj.sequence)
            .order_by("-sequence")
            .first()
        )
        if prev:
            return obj.distance_to(prev)
        return None


class NestedWaypointSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор для точек при создании/обновлении маршрута."""

    id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Waypoint
        fields = [
            "id",
            "order",
            "point_type",
            "address",
            "latitude",
            "longitude",
            "sequence",
            "scheduled_arrival",
            "notes",
        ]


class RouteDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор маршрута с вложенными точками."""

    waypoints = WaypointSerializer(many=True, read_only=True)
    order_ids = serializers.PrimaryKeyRelatedField(
        source="orders", many=True, read_only=True
    )
    vehicle_plate = serializers.CharField(source="vehicle.plate_number", read_only=True)
    vehicle_type_display = serializers.CharField(
        source="vehicle.get_vehicle_type_display", read_only=True
    )
    driver_name = serializers.CharField(
        source="driver.full_name", read_only=True, allow_null=True
    )
    driver_phone = serializers.CharField(source="driver.phone", read_only=True)
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    total_weight_kg = serializers.ReadOnlyField()
    total_volume_m3 = serializers.ReadOnlyField()
    load_percentage_weight = serializers.ReadOnlyField()
    load_percentage_volume = serializers.ReadOnlyField()
    load_validation_errors = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = [
            "id",
            "name",
            "status",
            "status_display",
            "orders",
            "order_ids",
            "vehicle",
            "vehicle_plate",
            "vehicle_type_display",
            "driver",
            "driver_name",
            "driver_phone",
            "total_distance_km",
            "estimated_time_hours",
            "estimated_fuel_l",
            "actual_distance_km",
            "actual_fuel_l",
            "departure_datetime",
            "estimated_completion_datetime",
            "completed_at",
            "notes",
            "is_active",
            "total_weight_kg",
            "total_volume_m3",
            "load_percentage_weight",
            "load_percentage_volume",
            "load_validation_errors",
            "waypoints",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "total_distance_km",
            "estimated_time_hours",
            "estimated_fuel_l",
            "completed_at",
        ]

    def get_load_validation_errors(self, obj):
        return obj.validate_load()


class RouteCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания маршрута с вложенными точками."""

    waypoints = NestedWaypointSerializer(many=True, required=False)
    order_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Route
        fields = [
            "id",
            "name",
            "vehicle",
            "driver",
            "departure_datetime",
            "notes",
            "waypoints",
            "order_ids",
        ]

    def create(self, validated_data):
        waypoints_data = validated_data.pop("waypoints", [])
        order_ids = validated_data.pop("order_ids", [])

        route = Route.objects.create(**validated_data)

        # Добавить точки из вложенных данных
        for wp_data in waypoints_data:
            Waypoint.objects.create(route=route, **wp_data)

        # Если переданы order_ids — автоматически создать точки погрузки/разгрузки
        if order_ids:
            from orders.models import Order

            for order_id in order_ids:
                try:
                    order = Order.objects.get(pk=order_id)
                    route.add_waypoint_from_order(order)
                except Order.DoesNotExist:
                    pass

        # Пересчитать расстояние и время
        route.calculate_distance_and_time()
        return route

    def update(self, instance, validated_data):
        waypoints_data = validated_data.pop("waypoints", None)
        order_ids = validated_data.pop("order_ids", None)

        # Обновить обычные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Пересоздать точки если переданы
        if waypoints_data is not None:
            instance.waypoints.all().delete()
            for wp_data in waypoints_data:
                Waypoint.objects.create(route=instance, **wp_data)

        # Добавить заказы
        if order_ids is not None:
            from orders.models import Order

            for order_id in order_ids:
                try:
                    order = Order.objects.get(pk=order_id)
                    if order not in instance.orders.all():
                        instance.add_waypoint_from_order(order)
                except Order.DoesNotExist:
                    pass

        instance.calculate_distance_and_time()
        return instance
