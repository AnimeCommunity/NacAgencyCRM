from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Cliente
from .serializers import ClientSerializer
from CRM.permissions import RolePermission

class ClientViewSet(ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [RolePermission]
