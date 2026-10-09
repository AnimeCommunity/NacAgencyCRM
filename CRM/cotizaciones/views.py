from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet

from CRM.permissions import RolePermission
from .models import Cotizacion
from .serializers import QuotationSerializer
from .utils import export_quotations_xlsx


class QuotationViewSet(ModelViewSet):
    queryset = Cotizacion.objects.select_related(
        "projecto", "projecto__cliente", "projecto__responsable"
    ).prefetch_related("items")
    serializer_class = QuotationSerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": {"sales", "production"},
        "retrieve": {"sales", "production"},
        "create": {"sales"},
        "update": {"sales"},
        "partial_update": {"sales"},
        "destroy": set(),
        "export": {"sales"},
    }

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        return export_quotations_xlsx(self.get_queryset().order_by("-created_at", "-id"))
