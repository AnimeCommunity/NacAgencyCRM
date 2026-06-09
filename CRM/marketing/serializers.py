from rest_framework import serializers
from .models import PlantillaMensaje, ConfigSMTP

class PlantillaMensajeSerializer(serializers.ModelSerializer):
    # Mostramos el texto  del tipo en el frontend
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = PlantillaMensaje
        fields = ['id', 'nombre', 'tipo', 'tipo_display', 'asunto', 'contenido', 'created_at']
        read_only_fields = ['id', 'created_at']


class ConfigSMTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigSMTP
        fields = '__all__'
        read_only_fields = ['id']
        
    
        # Esto hace que la contraseña se pueda guardar/escribir desde el front
        extra_kwargs = {
            'email_password': {'write_only': True}
        }