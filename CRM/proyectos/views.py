from rest_framework.viewsets import ModelViewSet

from CRM.permissions import RolePermission
from .models import Proyecto
from .serializers import ProjectDetailSerializer, ProjectSerializer


class ProjectViewSet(ModelViewSet):
    queryset = Proyecto.objects.select_related("cliente", "responsable")
    permission_classes = [RolePermission]
    role_permissions = {
        "list": {"sales", "production"},
        "retrieve": {"sales", "production"},
        "create": {"sales"},
        "update": {"sales"},
        "partial_update": {"sales"},
        "destroy": set(),
    }

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ProjectDetailSerializer
        return ProjectSerializer
