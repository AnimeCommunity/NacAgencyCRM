from rest_framework.viewsets import ModelViewSet

from CRM.permissions import RolePermission
from .models import Interaccion
from .serializers import InteractionSerializer


class InteractionViewSet(ModelViewSet):
    queryset = Interaccion.objects.select_related("cliente", "created_by")
    serializer_class = InteractionSerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": {"sales", "production"},
        "retrieve": {"sales", "production"},
        "create": {"sales", "production"},
        "update": {"sales", "production"},
        "partial_update": {"sales", "production"},
        "destroy": {"sales"},
    }

    def get_queryset(self):
        queryset = Interaccion.objects.select_related("cliente", "created_by")
        cliente_id = self.request.query_params.get("cliente")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
