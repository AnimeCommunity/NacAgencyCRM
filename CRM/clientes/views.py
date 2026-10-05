from rest_framework.viewsets import ModelViewSet

from CRM.permissions import RolePermission
from .models import Cliente
from .serializers import ClientSerializer


class ClienteViewSet(ModelViewSet):
    queryset = Cliente.objects.all().order_by("-created_at", "-id")
    serializer_class = ClientSerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": {"sales", "production"},
        "retrieve": {"sales", "production"},
        "create": {"sales"},
        "update": {"sales"},
        "partial_update": {"sales"},
        "destroy": set(),
    }
