from django.db import models


#Se crean los modelos para los clientes
class Cliente(models.Model):
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('natural', 'Natural'),
            ('empresa', 'Empresa')
        ],
        default='natural')
    nombre = models.CharField(max_length=100) # Nombre del cliente
    telefono = models.CharField(max_length=20, blank=True, null=True) # Telefono del cliente
    email = models.EmailField(unique=True) # Email del cliente
    empresa = models.CharField(max_length=100, blank=True, null=True) # Empresa del cliente
    #estado del cliente
    estado = models.CharField(
        max_length=50,
        choices=[
            ('activo', 'Activo'),
            ('inactivo', 'Inactivo'),
            ('potencial', 'Potencial')
        ],
        default='potencial'
    )
    ciudad = models.CharField(max_length=100, blank=True, null=True) # Ciudad del cliente
    fecha_registro = models.DateField(auto_now_add=True) # Fecha de registro del cliente
    notas = models.TextField(blank=True, null=True) # Notas adicionales sobre el cliente

    def __str__(self):
        return f"{self.nombre} ({self.email})" # como se muestra el cliente en el admin
