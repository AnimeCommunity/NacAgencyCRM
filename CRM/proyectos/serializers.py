from rest_framework import serializers
from django.utils import timezone

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
        pagado = attrs.get("pagado", getattr(self.instance, "pagado", False))
        fecha_pago = attrs.get(
            "fecha_pago", getattr(self.instance, "fecha_pago", None)
        )
        errors = {}
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            errors["fecha_fin"] = "La fecha de fin no puede ser anterior al inicio."
        if presupuesto is not None and presupuesto < 0:
            errors["presupuesto_estimado"] = "El presupuesto no puede ser negativo."
        if pagado and not fecha_pago:
            errors["fecha_pago"] = "Registra la fecha en que se confirmó el pago."
        if not pagado and fecha_pago:
            errors["fecha_pago"] = "Un proyecto sin pago no puede tener fecha de pago."
        if fecha_pago and fecha_pago > timezone.localdate():
            errors["fecha_pago"] = "La fecha de pago no puede estar en el futuro."
        nuevo_estado = attrs.get("estado")
        if self.instance and nuevo_estado and nuevo_estado != self.instance.estado:
            if self.instance.estado in {"finalizado", "cancelado"}:
                errors["estado"] = "El estado de este proyecto ya no puede modificarse."
            elif nuevo_estado == "cancelado":
                errors["estado"] = "Usa la acción de cancelación del proyecto."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class ProjectDetailSerializer(serializers.ModelSerializer):
    cliente = ClientSerializer(read_only=True)
    responsable = UserSerializer(read_only=True)

    class Meta:
        model = Proyecto
        fields = "__all__"
