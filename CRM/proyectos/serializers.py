from rest_framework import serializers

from clientes.models import Cliente
from users.models import User
from .models import Proyecto
from clientes.serializers import ClientSerializer
from users.serializers import UserSerializer


class ProjectSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    responsable = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Proyecto
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

class ProjectDetailSerializer(serializers.ModelSerializer):
    cliente = ClientSerializer(read_only=True)
    responsable = UserSerializer(read_only=True)

    class Meta:
        model = Proyecto
        fields = '__all__'
