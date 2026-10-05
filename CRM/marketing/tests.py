from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import override_settings
from openpyxl import load_workbook
from rest_framework import status
from rest_framework.test import APITestCase

from clientes.models import Cliente
from cotizaciones.models import Cotizacion
from marketing.models import ConfigSMTP, PlantillaMensaje
from proyectos.models import Proyecto


User = get_user_model()


class MarketingAndExportTests(APITestCase):
    def setUp(self):
        self.sales = User.objects.create_user(
            username="sales", password="StrongPass!2026", role="sales"
        )
        self.production = User.objects.create_user(
            username="production", password="StrongPass!2026", role="production"
        )
        Cliente.objects.create(
            nombre="ACME", email="acme@example.com", origen="web"
        )

    def test_sales_export_returns_valid_xlsx(self):
        self.client.force_authenticate(self.sales)
        response = self.client.get("/api/marketing/export-excel/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(BytesIO(response.content))
        self.assertEqual(workbook["Reporte de Clientes"]["A2"].value, "ACME")

    def test_production_cannot_manage_smtp_configuration(self):
        self.client.force_authenticate(self.production)
        response = self.client.post(
            "/api/marketing-config/",
            {
                "email_usuario": "smtp@example.com",
                "servidor_host": "smtp.example.com",
                "puerto": 587,
                "use_tls": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_smtp_configuration_is_rejected(self):
        admin = User.objects.create_user(
            username="admin-smtp-duplicate", password="StrongPass!2026", role="admin"
        )
        ConfigSMTP.objects.create(
            email_usuario="first@example.com", servidor_host="smtp.example.com"
        )
        self.client.force_authenticate(admin)

        response = self.client.post(
            "/api/marketing-config/",
            {
                "email_usuario": "second@example.com",
                "servidor_host": "smtp.example.com",
                "puerto": 587,
                "use_tls": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_smtp_singleton_is_enforced_by_database(self):
        ConfigSMTP.objects.create(
            email_usuario="first-db@example.com", servidor_host="smtp.example.com"
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ConfigSMTP.objects.create(
                email_usuario="second-db@example.com", servidor_host="smtp.example.com"
            )

    def test_admin_smtp_update_does_not_persist_password(self):
        admin = User.objects.create_user(
            username="admin-smtp", password="StrongPass!2026", role="admin"
        )
        self.client.force_authenticate(admin)

        response = self.client.post(
            "/api/marketing-config/",
            {
                "email_usuario": "smtp@example.com",
                "email_password": "must-not-be-stored",
                "servidor_host": "smtp.example.com",
                "puerto": 587,
                "use_tls": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        config = ConfigSMTP.objects.get()
        self.assertEqual(config.email_password, "")
        self.assertNotIn("email_password", response.data)

    @override_settings(
        CRM_SMTP_PASSWORD="test-password",
        CRM_SMTP_ALLOWED_HOSTS=["smtp.example.com"],
    )
    def test_campaign_rejects_smtp_host_outside_allowlist(self):
        self.client.force_authenticate(self.sales)
        cliente = Cliente.objects.get(email="acme@example.com")
        plantilla = PlantillaMensaje.objects.create(
            nombre="Seguimiento",
            tipo="email",
            asunto="Hola",
            contenido="Hola {nombre}",
        )
        ConfigSMTP.objects.create(
            email_usuario="smtp@example.com",
            email_password="legacy-password",
            servidor_host="127.0.0.1",
            puerto=25,
            use_tls=False,
        )

        response = self.client.post(
            "/api/marketing/enviar-campana/",
            {"cliente_id": cliente.id, "plantilla_id": plantilla.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("permitido", response.data["error"])


class ManagerialReportTests(APITestCase):
    def setUp(self):
        self.sales = User.objects.create_user(
            username="sales-report", password="StrongPass!2026", role="sales"
        )
        customer = Cliente.objects.create(
            nombre="Cliente reportes", email="reports@example.com"
        )
        project = Proyecto.objects.create(
            cliente=customer,
            nombre="Evento",
            descripcion="Evento",
            tipo_evento="show",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=1),
            presupuesto_estimado=Decimal("500.00"),
            responsable=self.sales,
        )
        Cotizacion.objects.create(
            projecto=project,
            numero="A-1",
            subtotal=Decimal("100.00"),
            impuestos=Decimal("19.00"),
            total=Decimal("119.00"),
            estado="aceptada",
            fecha_vencimiento=date.today() + timedelta(days=10),
        )
        Cotizacion.objects.create(
            projecto=project,
            numero="R-1",
            subtotal=Decimal("900.00"),
            impuestos=Decimal("171.00"),
            total=Decimal("1071.00"),
            estado="rechazada",
            fecha_vencimiento=date.today() + timedelta(days=10),
        )

    def test_production_can_read_managerial_report(self):
        production = User.objects.create_user(
            username="production-report", password="StrongPass!2026", role="production"
        )
        self.client.force_authenticate(production)

        response = self.client.get("/api/reports/gerencial/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_report_counts_projects_and_accepted_revenue_once(self):
        self.client.force_authenticate(self.sales)
        response = self.client.get("/api/reports/gerencial/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        metric = response.data["ingresos_por_tipo_evento"][0]
        top_client = response.data["top_5_clientes"][0]
        self.assertEqual(metric["cantidad_proyectos"], 1)
        self.assertEqual(Decimal(str(metric["total_generado"])), Decimal("119.00"))
        self.assertEqual(
            Decimal(str(top_client["total_invertido"])), Decimal("119.00")
        )
