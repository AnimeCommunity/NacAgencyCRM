from io import BytesIO

from django.urls import reverse
from openpyxl import load_workbook
from rest_framework import status
from rest_framework.test import APITestCase

from clientes.models import Cliente
from interacciones.models import Interaccion
from users.models import User


class InteraccionFlowTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sales-interacciones",
            password="StrongPass!123",
            role="sales",
        )
        self.client.force_authenticate(self.user)
        self.cliente = Cliente.objects.create(
            nombre="Maria Torres",
            email="maria@example.com",
            estado="activo"
        )
    # Prueba de creación de interacciones vía API
    def test_crear_interaccion(self):
        """Prueba el flujo completo de creación de interacciones"""
        url = reverse('interaccion-list')
        data = {
            "cliente": self.cliente.id,
            "tipo": "llamada",
            "resultado": "contactado",
            "descripcion": "Se realizó llamada de seguimiento."
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Interaccion.objects.count(), 1)
        self.assertEqual(Interaccion.objects.first().cliente.nombre, "Maria Torres")
        self.assertEqual(Interaccion.objects.first().resultado, "contactado")

    def test_rechaza_resultado_invalido(self):
        response = self.client.post(
            reverse('interaccion-list'),
            {
                "cliente": self.cliente.id,
                "tipo": "llamada",
                "resultado": "inventado",
                "descripcion": "Resultado inválido",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("resultado", response.data)

    def test_filtra_interacciones_por_resultado(self):
        Interaccion.objects.create(
            cliente=self.cliente,
            tipo="llamada",
            resultado="sin_respuesta",
            descripcion="No contestó",
        )
        Interaccion.objects.create(
            cliente=self.cliente,
            tipo="llamada",
            resultado="contactado",
            descripcion="Contestó",
        )

        response = self.client.get(reverse('interaccion-list'), {"resultado": "contactado"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["resultado"], "contactado")

    def test_exporta_historial_de_interacciones_a_xlsx(self):
        Interaccion.objects.create(
            cliente=self.cliente,
            tipo="llamada",
            resultado="sin_respuesta",
            descripcion="No contestó la llamada",
            created_by=self.user,
        )

        response = self.client.get(
            "/api/interactions/export/", {"cliente": self.cliente.id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(BytesIO(response.content))
        sheet = workbook["Interacciones"]
        self.assertEqual(sheet["A2"].value, "Maria Torres")
        self.assertEqual(sheet["C2"].value, "Sin respuesta")
        self.assertEqual(sheet["D2"].value, "No contestó la llamada")

    def test_production_can_create_interaction_but_cannot_bulk_export(self):
        production = User.objects.create_user(
            username="production-interacciones",
            password="StrongPass!123",
            role="production",
        )
        self.client.force_authenticate(production)

        created = self.client.post(
            reverse("interaccion-list"),
            {
                "cliente": self.cliente.id,
                "tipo": "llamada",
                "resultado": "contactado",
                "descripcion": "Seguimiento de producción",
            },
            format="json",
        )
        exported = self.client.get("/api/interactions/export/")

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(exported.status_code, status.HTTP_403_FORBIDDEN)
        
    # Prueba de listado de interacciones vía API
    def test_listar_interacciones(self):
        """Prueba que las interacciones se muestren correctamente"""
        Interaccion.objects.create(
            cliente=self.cliente,
            tipo="correo",
            descripcion="Correo de bienvenida"
        )
        url = reverse('interaccion-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
