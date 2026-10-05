from django.urls import reverse
from rest_framework.test import APITestCase

from clientes.models import Cliente
from users.models import User


class ClienteIntegrationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sales-clientes",
            password="StrongPass!123",
            role="sales",
        )
        self.client.force_authenticate(self.user)

    def test_crear_cliente(self):
        """Prueba que se pueda crear un cliente via API"""
        url = reverse('cliente-list')
        data = {
            "nombre": "Pedro Ruiz",
            "telefono": "3012223344",
            "email": "pedro@example.com",
            "empresa": "SoftCorp",
            "estado": "activo"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Cliente.objects.count(), 1)
    # Prueba de listado de clientes vía API
    def test_listar_clientes(self):
        """Prueba que la API liste los clientes existentes"""
        Cliente.objects.create(nombre="Ana", email="ana@example.com")
        url = reverse('cliente-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
