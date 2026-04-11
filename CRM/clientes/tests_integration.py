from rest_framework.test import APITestCase
from django.urls import reverse
from clientes.models import Cliente

# Pruebas de integración para el flujo de clientes
class ClienteIntegrationTest(APITestCase):
    # Configuración inicial para las pruebas
    def test_crear_cliente(self):
        """Prueba que se pueda crear un cliente via API"""
        url = reverse('cliente-list')  # el router crea esta ruta automáticamente
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
