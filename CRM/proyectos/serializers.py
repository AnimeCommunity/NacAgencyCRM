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
        fields = "__all__"
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        fecha_inicio = attrs.get("fecha_inicio", getattr(self.instance, "fecha_inicio", None))
        fecha_fin = attrs.get("fecha_fin", getattr(self.instance, "fecha_fin", None))
        presupuesto = attrs.get(
            "presupuesto_estimado",
            getattr(self.instance, "presupuesto_estimado", None),
        )
        errors = {}
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            errors["fecha_fin"] = "La fecha de fin no puede ser anterior al inicio."
        if presupuesto is not None and presupuesto < 0:
            errors["presupuesto_estimado"] = "El presupuesto no puede ser negativo."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class ProjectDetailSerializer(serializers.ModelSerializer):
    cliente = ClientSerializer(read_only=True)
    responsable = UserSerializer(read_only=True)

    class Meta:
        model = Proyecto
        fields = "__all__"
