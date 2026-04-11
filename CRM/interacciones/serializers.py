from rest_framework import serializers
from .models import Interaccion

class InteractionSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.id')

    class Meta:
        model = Interaccion
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
