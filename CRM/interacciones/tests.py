from rest_framework.test import APITestCase
from django.urls import reverse
from clientes.models import Cliente
from interacciones.models import Interaccion

# Pruebas de integración para el flujo de interacciones
class InteraccionFlowTest(APITestCase):
    # Configuración inicial para las pruebas
    def setUp(self):
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
            "descripcion": "Se realizó llamada de seguimiento."
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Interaccion.objects.count(), 1)
        self.assertEqual(Interaccion.objects.first().cliente.nombre, "Maria Torres")
        
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
