from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from clientes.models import Cliente
from proyectos.models import Proyecto
from .models import Cotizacion


User = get_user_model()


class QuotationApiTests(APITestCase):
    def setUp(self):
        self.sales = User.objects.create_user(
            username="sales", password="StrongPass!2026", role="sales"
        )
        self.production = User.objects.create_user(
            username="production", password="StrongPass!2026", role="production"
        )
        self.client_record = Cliente.objects.create(
            nombre="Cliente", email="cliente@example.com"
        )
        self.project = Proyecto.objects.create(
            cliente=self.client_record,
            nombre="Proyecto",
            descripcion="Proyecto de prueba",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            presupuesto_estimado=Decimal("1000.00"),
            responsable=self.sales,
        )

    def quotation_payload(self):
        return {
            "projecto": self.project.id,
            "numero": "Q-001",
            "fecha_vencimiento": str(date.today() + timedelta(days=15)),
            "notas": "Prueba",
            "items": [
                {
                    "descripcion": "Producción audiovisual",
                    "cantidad": 2,
                    "precio_unitario": "100.00",
                }
            ],
        }

    def test_sales_can_create_atomic_quotation_with_server_totals(self):
        self.client.force_authenticate(self.sales)
        response = self.client.post(
            "/api/quotations/", self.quotation_payload(), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        quotation = Cotizacion.objects.get(numero="Q-001")
        self.assertEqual(quotation.subtotal, Decimal("200.00"))
        self.assertEqual(quotation.impuestos, Decimal("38.00"))
        self.assertEqual(quotation.total, Decimal("238.00"))
        self.assertEqual(quotation.items.get().total, Decimal("200.00"))

    def test_invalid_item_rolls_back_quotation(self):
        self.client.force_authenticate(self.sales)
        payload = self.quotation_payload()
        payload["numero"] = "Q-INVALID"
        payload["items"][0]["cantidad"] = -1

        response = self.client.post("/api/quotations/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Cotizacion.objects.filter(numero="Q-INVALID").exists())

    def test_update_rejects_empty_item_list(self):
        self.client.force_authenticate(self.sales)
        created = self.client.post(
            "/api/quotations/", self.quotation_payload(), format="json"
        )

        response = self.client.patch(
            f"/api/quotations/{created.data['id']}/", {"items": []}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("items", response.data)

    def test_production_cannot_create_quotation(self):
        self.client.force_authenticate(self.production)
        response = self.client.post(
            "/api/quotations/", self.quotation_payload(), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
