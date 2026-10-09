from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers
from .models import PlantillaMensaje, ConfigSMTP
from .smtp_secrets import encrypt_smtp_password

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
    password_configurada = serializers.SerializerMethodField()

    class Meta:
        model = ConfigSMTP
        fields = [
            "id",
            "email_usuario",
            "email_password",
            "password_configurada",
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
        password = attrs.get("email_password", "")
        if self.instance is None and not password:
            raise serializers.ValidationError(
                {"email_password": "Ingresa la contraseña o clave de aplicación SMTP."}
            )
        return attrs

    def get_password_configurada(self, instance):
        return bool(
            instance.email_password or getattr(settings, "CRM_SMTP_PASSWORD", "")
        )

    def create(self, validated_data):
        password = validated_data.pop("email_password")
        try:
            encrypted_password = encrypt_smtp_password(password)
        except ImproperlyConfigured as exc:
            raise serializers.ValidationError(
                {"email_password": str(exc)}
            ) from exc
        return super().create(
            {**validated_data, "email_password": encrypted_password}
        )

    def update(self, instance, validated_data):
        password = validated_data.pop("email_password", "")
        if password:
            try:
                validated_data["email_password"] = encrypt_smtp_password(password)
            except ImproperlyConfigured as exc:
                raise serializers.ValidationError(
                    {"email_password": str(exc)}
                ) from exc
        return super().update(instance, validated_data)
