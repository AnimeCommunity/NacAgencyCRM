from rest_framework import serializers
from .models import Cliente

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ClientDetailSerializer(ClientSerializer):
    projects_count = serializers.IntegerField(read_only=True)

    class Meta(ClientSerializer.Meta):
        fields = ClientSerializer.Meta.fields + ['projects_count']
