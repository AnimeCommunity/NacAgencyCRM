from django.db import models
from clientes.models import Cliente

# Modelo para las interacciones con los clientes
class Interaccion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='interacciones') # Relacion con el cliente
    # Tipo de interaccion
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('llamada', 'Llamada'),
            ('correo', 'Correo'),
            ('reunión', 'Reunión'),
            ('seguimiento', 'Seguimiento')
        ]
    )
    descripcion = models.TextField() # Descripcion de la interaccion
    fecha = models.DateTimeField(auto_now_add=True) # Fecha de la interaccion

    def __str__(self):
        return f"{self.tipo} - {self.cliente.nombre}" # como se muestra la interaccion en el admin
