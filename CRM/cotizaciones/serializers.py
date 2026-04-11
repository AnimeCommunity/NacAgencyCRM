from rest_framework import serializers
from .models import Cotizacion, CotizacionItem

class QuotationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CotizacionItem
        fields = '__all__'
        read_only_fields = ['id']

class QuotationSerializer(serializers.ModelSerializer):
    items = QuotationItemSerializer(many=True)

    class Meta:
        model = Cotizacion
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        quotation = Cotizacion.objects.create(**validated_data)

        for item in items_data:
            CotizacionItem.objects.create(
                quotation=quotation,
                **item
            )

        return quotation
