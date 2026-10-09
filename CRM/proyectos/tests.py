from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
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

    def test_paid_project_requires_payment_date(self):
        self.client.force_authenticate(self.sales)
        payload = self.payload()
        payload["pagado"] = True
        payload["fecha_pago"] = None

        response = self.client.post("/api/projects/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_pago", response.data)

    def test_unpaid_project_rejects_payment_date(self):
        self.client.force_authenticate(self.sales)
        payload = self.payload()
        payload["pagado"] = False
        payload["fecha_pago"] = str(date.today())

        response = self.client.post("/api/projects/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_pago", response.data)

    def test_paid_project_rejects_future_payment_date(self):
        self.client.force_authenticate(self.sales)
        payload = self.payload()
        payload["pagado"] = True
        payload["fecha_pago"] = str(date.today() + timedelta(days=1))

        response = self.client.post("/api/projects/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fecha_pago", response.data)

    def test_database_rejects_payment_date_for_unpaid_project(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Proyecto.objects.create(
                cliente=self.client_record,
                nombre="Pago contradictorio",
                descripcion="Proyecto inválido",
                tipo_evento="show",
                fecha_inicio=date.today(),
                fecha_fin=date.today() + timedelta(days=1),
                presupuesto_estimado="1000.00",
                pagado=False,
                fecha_pago=date.today(),
                responsable=self.sales,
            )

    def test_sales_can_cancel_active_project(self):
        project = Proyecto.objects.create(
            cliente=self.client_record,
            nombre="Proyecto cancelable",
            descripcion="Proyecto de prueba",
            tipo_evento="show",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            presupuesto_estimado="1000.00",
            estado="en_proceso",
            responsable=self.sales,
        )
        self.client.force_authenticate(self.sales)

        response = self.client.post(f"/api/projects/{project.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.estado, "cancelado")

    def test_finalized_project_cannot_be_cancelled(self):
        project = Proyecto.objects.create(
            cliente=self.client_record,
            nombre="Proyecto finalizado",
            descripcion="Proyecto de prueba",
            tipo_evento="show",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            presupuesto_estimado="1000.00",
            estado="finalizado",
            responsable=self.sales,
        )
        self.client.force_authenticate(self.sales)

        response = self.client.post(f"/api/projects/{project.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        project.refresh_from_db()
        self.assertEqual(project.estado, "finalizado")

    def test_finalized_project_cannot_be_cancelled_through_patch(self):
        project = Proyecto.objects.create(
            cliente=self.client_record,
            nombre="Finalizado protegido",
            descripcion="Proyecto de prueba",
            tipo_evento="show",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            presupuesto_estimado="1000.00",
            estado="finalizado",
            responsable=self.sales,
        )
        self.client.force_authenticate(self.sales)

        response = self.client.patch(
            f"/api/projects/{project.id}/", {"estado": "cancelado"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        project.refresh_from_db()
        self.assertEqual(project.estado, "finalizado")

    def test_active_project_must_use_cancel_action(self):
        project = Proyecto.objects.create(
            cliente=self.client_record,
            nombre="Cancelación controlada",
            descripcion="Proyecto de prueba",
            tipo_evento="show",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            presupuesto_estimado="1000.00",
            estado="en_proceso",
            responsable=self.sales,
        )
        self.client.force_authenticate(self.sales)

        response = self.client.patch(
            f"/api/projects/{project.id}/", {"estado": "cancelado"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_missing_project_returns_not_found(self):
        self.client.force_authenticate(self.sales)

        response = self.client.post("/api/projects/999999/cancel/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_locks_project_before_writing(self):
        project = Proyecto.objects.create(
            cliente=self.client_record,
            nombre="Actualización protegida",
            descripcion="Proyecto de prueba",
            tipo_evento="show",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            presupuesto_estimado="1000.00",
            estado="propuesta",
            responsable=self.sales,
        )
        self.client.force_authenticate(self.sales)

        with patch(
            "proyectos.views.Proyecto.objects.select_for_update",
            wraps=Proyecto.objects.select_for_update,
        ) as select_for_update:
            response = self.client.patch(
                f"/api/projects/{project.id}/",
                {"estado": "aprobado"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        select_for_update.assert_called_once_with()

    def test_production_cannot_cancel_project(self):
        project = Proyecto.objects.create(
            cliente=self.client_record,
            nombre="Proyecto protegido",
            descripcion="Proyecto de prueba",
            tipo_evento="show",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            presupuesto_estimado="1000.00",
            responsable=self.sales,
        )
        self.client.force_authenticate(self.production)

        response = self.client.post(f"/api/projects/{project.id}/cancel/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
