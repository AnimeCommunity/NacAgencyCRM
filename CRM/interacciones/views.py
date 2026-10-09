from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from CRM.permissions import RolePermission
from .models import Interaccion
from .serializers import InteractionSerializer
from .utils import export_interactions_xlsx


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
        "export": {"sales"},
    }

    def get_queryset(self):
        queryset = Interaccion.objects.select_related("cliente", "created_by")
        cliente_id = self.request.query_params.get("cliente")
        resultado = self.request.query_params.get("resultado")
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if resultado:
            queryset = queryset.filter(resultado=resultado)
        return queryset.order_by("-created_at")

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        return export_interactions_xlsx(self.get_queryset())

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
