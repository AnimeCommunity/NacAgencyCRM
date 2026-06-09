from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Interaccion
from .serializers import InteractionSerializer

class InteractionViewSet(ModelViewSet):

    queryset = Interaccion.objects.select_related('cliente') 
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]