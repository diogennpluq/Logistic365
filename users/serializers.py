"""DRF Serializers for Users app."""

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading user data."""

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_display",
            "phone",
            "avatar",
            "is_active",
            "is_admin",
            "is_dispatcher",
            "is_driver",
            "is_accountant",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "is_admin",
            "is_dispatcher",
            "is_driver",
            "is_accountant",
            "created_at",
            "updated_at",
        )


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user with password hashing."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "phone",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
