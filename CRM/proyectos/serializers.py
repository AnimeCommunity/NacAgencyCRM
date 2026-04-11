from rest_framework import serializers
from .models import Project
from clientes.serializers import ClientSerializer
from users.serializers import UserSerializer

class ProjectSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(read_only=False)
    responsible = serializers.PrimaryKeyRelatedField(read_only=False)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

class ProjectDetailSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    responsible = UserSerializer(read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
