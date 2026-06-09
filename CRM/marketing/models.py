from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Objetivo(models.Model):
    TIPO_OBJETIVO = [
        ('clientes', 'Nuevos Clientes'),
        ('ventas', 'Ventas Cerradas'),
        ('monto', 'Monto Facturado ($)'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='objetivos'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_OBJETIVO)
    meta_valor = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.tipo} - {self.usuario.username} ({self.meta_valor})"

class PlantillaMensaje(models.Model):
    TIPO_CHOICES = (
        ('email', 'Correo Electrónico (SMTP)'),
        ('whatsapp', 'WhatsApp URL'),
    )
    nombre = models.CharField(max_length=100) 
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    asunto = models.CharField(max_length=200, blank=True, null=True) # Solo para Email
    contenido = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

class ConfigSMTP(models.Model):
    email_usuario = models.EmailField(max_length=150, help_text="Correo desde el que se enviarán los mensajes")
    email_password = models.CharField(max_length=255, help_text="Contraseña o Token de aplicación")
    servidor_host = models.CharField(max_length=100, default="smtp.gmail.com")
    puerto = models.IntegerField(default=587)
    use_tls = models.BooleanField(default=True)

    def __str__(self):
        return f"Configuración SMTP: {self.email_usuario}"