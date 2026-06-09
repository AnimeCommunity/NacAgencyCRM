from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Proyecto
from .serializers import ProjectSerializer, ProjectDetailSerializer

class ProjectViewSet(ModelViewSet):
    queryset = Proyecto.objects.select_related('cliente', 'responsable')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ProjectDetailSerializer
        return ProjectSerializer
