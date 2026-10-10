from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from openpyxl import load_workbook
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
        quotation = Cotizacion.objects.get(id=response.data["id"])
        self.assertEqual(quotation.numero, f"COT-{date.today().year}-{quotation.id:06d}")
        self.assertEqual(response.data["numero"], quotation.numero)
        self.assertEqual(quotation.subtotal, Decimal("200.00"))
        self.assertEqual(quotation.impuestos, Decimal("38.00"))
        self.assertEqual(quotation.total, Decimal("238.00"))
        self.assertEqual(quotation.items.get().total, Decimal("200.00"))

    def test_quotation_numbers_are_generated_in_sequence_and_ignore_manual_values(self):
        self.client.force_authenticate(self.sales)
        first_response = self.client.post(
            "/api/quotations/",
            {**self.quotation_payload(), "numero": "MANUAL-001"},
            format="json",
        )
        second_response = self.client.post(
            "/api/quotations/", self.quotation_payload(), format="json"
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        first = Cotizacion.objects.get(id=first_response.data["id"])
        second = Cotizacion.objects.get(id=second_response.data["id"])
        self.assertEqual(first.numero, f"COT-{date.today().year}-{first.id:06d}")
        self.assertEqual(second.numero, f"COT-{date.today().year}-{second.id:06d}")
        self.assertGreater(second.id, first.id)
        self.assertNotEqual(first.numero, "MANUAL-001")

    def test_invalid_item_rolls_back_quotation(self):
        self.client.force_authenticate(self.sales)
        payload = self.quotation_payload()
        payload["items"][0]["cantidad"] = -1

        response = self.client.post("/api/quotations/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Cotizacion.objects.count(), 0)

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

    def test_sales_can_export_quotation_history_as_xlsx(self):
        self.client.force_authenticate(self.sales)
        created = self.client.post(
            "/api/quotations/", self.quotation_payload(), format="json"
        )

        response = self.client.get("/api/quotations/export/")

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        workbook = load_workbook(BytesIO(response.content))
        sheet = workbook["Cotizaciones"]
        self.assertEqual(sheet["A2"].value, created.data["numero"])
        self.assertEqual(sheet["B2"].value, "Proyecto")
        self.assertEqual(sheet["C2"].value, "Cliente")

    def test_production_cannot_bulk_export_quotation_history(self):
        self.client.force_authenticate(self.production)

        response = self.client.get("/api/quotations/export/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
