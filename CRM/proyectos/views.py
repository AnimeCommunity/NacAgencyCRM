from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Project
from .serializers import ProjectSerializer, ProjectDetailSerializer

class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.select_related('client', 'responsible')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ProjectDetailSerializer
        return ProjectSerializer
