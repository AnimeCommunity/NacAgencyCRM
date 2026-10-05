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
    email_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )

    class Meta:
        model = ConfigSMTP
        fields = [
            "id",
            "email_usuario",
            "email_password",
            "servidor_host",
            "puerto",
            "use_tls",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if self.instance is None and ConfigSMTP.objects.exists():
            raise serializers.ValidationError(
                "Solo puede existir una configuración SMTP. Actualiza la existente."
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("email_password", None)
        return super().create({**validated_data, "email_password": ""})

    def update(self, instance, validated_data):
        validated_data.pop("email_password", None)
        instance.email_password = ""
        return super().update(instance, validated_data)
