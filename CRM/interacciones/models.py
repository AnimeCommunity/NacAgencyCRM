from django.db import models
from clientes.models import Cliente
from django.conf import settings


class Interaccion(models.Model):
    TIPO_CHOICES = [
        ('llamada', 'Llamada'),
        ('correo_manual', 'Correo Manual'),
        ('reunión', 'Reunión'),
        ('seguimiento', 'Seguimiento'),
        ('email_marketing', 'Campaña de Email (Automatizada)'), 
        ('whatsapp_link', 'Enlace de WhatsApp Generado'),        
    ]
    
    RESULTADO_CHOICES = [
        ('sin_definir', 'Sin definir'),
        ('contactado', 'Contactado'),
        ('sin_respuesta', 'Sin respuesta'),
        ('interesado', 'Interesado'),
        ('no_interesado', 'No interesado'),
        ('reunion_agendada', 'Reunión agendada'),
        ('cerrado', 'Cierre concretado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='interacciones')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    resultado = models.CharField(
        max_length=30,
        choices=RESULTADO_CHOICES,
        default='sin_definir',
    )
    descripcion = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente.nombre} ({self.created_at:%Y-%m-%d})"
