"""DRF API Views for Users app."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import UserCreateSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing User objects.

    list   — GET  /api/users/
    create — POST /api/users/
    retrieve — GET  /api/users/{id}/
    update — PUT  /api/users/{id}/
    destroy — DELETE /api/users/{id}/
    """

    permission_classes = [IsAuthenticated]
    search_fields = ["username", "email", "first_name", "last_name", "phone"]
    ordering_fields = ["username", "email", "role", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer
