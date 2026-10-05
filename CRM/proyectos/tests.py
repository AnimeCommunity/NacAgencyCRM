from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from clientes.models import Cliente
from .models import Proyecto


User = get_user_model()


class ProjectValidationTests(APITestCase):
    def setUp(self):
        self.sales = User.objects.create_user(
            username="sales", password="StrongPass!2026", role="sales"
        )
        self.production = User.objects.create_user(
            username="production", password="StrongPass!2026", role="production"
        )
        self.client_record = Cliente.objects.create(
            nombre="Cliente", email="project@example.com"
        )

    def payload(self):
        return {
            "cliente": self.client_record.id,
            "nombre": "Proyecto",
            "descripcion": "Proyecto de prueba",
            "tipo_evento": "show",
            "fecha_inicio": str(date.today()),
            "fecha_fin": str(date.today() + timedelta(days=2)),
            "presupuesto_estimado": "1000.00",
            "estado": "propuesta",
            "responsable": self.sales.id,
        }

    def test_project_rejects_invalid_dates_and_negative_budget(self):
        self.client.force_authenticate(self.sales)
        payload = self.payload()
        payload["fecha_fin"] = str(date.today() - timedelta(days=1))
        payload["presupuesto_estimado"] = "-1.00"

        response = self.client.post("/api/projects/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_fin", response.data)
        self.assertIn("presupuesto_estimado", response.data)
        self.assertEqual(Proyecto.objects.count(), 0)

    def test_production_cannot_create_project(self):
        self.client.force_authenticate(self.production)
        response = self.client.post("/api/projects/", self.payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
