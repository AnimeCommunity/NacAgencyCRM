from rest_framework.viewsets import ModelViewSet

from CRM.permissions import RolePermission
from .models import Cotizacion
from .serializers import QuotationSerializer


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
    }
