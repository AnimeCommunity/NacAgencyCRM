from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Cotizacion
from .serializers import QuotationSerializer

class QuotationViewSet(ModelViewSet):
    queryset = Cotizacion.objects.prefetch_related('items')
    serializer_class = QuotationSerializer
    permission_classes = [IsAuthenticated]
