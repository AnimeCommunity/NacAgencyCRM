from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Interaction
from .serializers import InteractionSerializer

class InteractionViewSet(ModelViewSet):
    queryset = Interaction.objects.select_related(
        'client', 'project', 'created_by'
    )
    serializer_class = InteractionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
