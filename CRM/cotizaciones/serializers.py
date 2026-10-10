from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Cotizacion, CotizacionItem


TAX_RATE = serializers.DecimalField(max_digits=4, decimal_places=2).to_internal_value("0.19")


class QuotationItemSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CotizacionItem
        fields = ["id", "descripcion", "cantidad", "precio_unitario", "total"]
        read_only_fields = ["id", "total"]

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
        return value

    def validate_precio_unitario(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio unitario debe ser mayor que cero.")
        return value


class QuotationSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    impuestos = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cotizacion
        fields = [
            "id",
            "projecto",
            "numero",
            "subtotal",
            "impuestos",
            "total",
            "estado",
            "created_at",
            "fecha_vencimiento",
            "notas",
            "items",
        ]
        read_only_fields = [
            "id",
            "numero",
            "subtotal",
            "impuestos",
            "total",
            "created_at",
        ]

    def validate(self, attrs):
        items = attrs.get("items")
        if items is not None and not items:
            raise serializers.ValidationError({"items": "Agrega al menos un ítem."})
        if attrs.get("fecha_vencimiento") and attrs["fecha_vencimiento"] < timezone.localdate():
            raise serializers.ValidationError(
                {"fecha_vencimiento": "La fecha de vencimiento no puede estar en el pasado."}
            )
        return attrs

    @staticmethod
    def _totals(items_data):
        subtotal = sum(
            item["cantidad"] * item["precio_unitario"] for item in items_data
        )
        impuestos = (subtotal * TAX_RATE).quantize(subtotal.as_tuple().exponent)
        return subtotal, impuestos, subtotal + impuestos

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        subtotal, impuestos, total = self._totals(items_data)
        quotation = Cotizacion.objects.create(
            numero=None,
            subtotal=subtotal,
            impuestos=impuestos,
            total=total,
            **validated_data,
        )
        quotation.numero = f"COT-{timezone.localdate().year}-{quotation.id:06d}"
        quotation.save(update_fields=["numero"])
        CotizacionItem.objects.bulk_create(
            [
                CotizacionItem(
                    cotizacion=quotation,
                    total=item["cantidad"] * item["precio_unitario"],
                    **item,
                )
                for item in items_data
            ]
        )
        return quotation

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)
        if items_data is not None:
            subtotal, impuestos, total = self._totals(items_data)
            instance.subtotal = subtotal
            instance.impuestos = impuestos
            instance.total = total
            instance.items.all().delete()
            CotizacionItem.objects.bulk_create(
                [
                    CotizacionItem(
                        cotizacion=instance,
                        total=item["cantidad"] * item["precio_unitario"],
                        **item,
                    )
                    for item in items_data
                ]
            )
        instance.save()
        return instance
