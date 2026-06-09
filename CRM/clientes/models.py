from django.db import models

class Cliente(models.Model):
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('natural', 'Natural'),
            ('empresa', 'Empresa')
        ],
        default='natural')
    nombre = models.CharField(max_length=100) 
    telefono = models.CharField(max_length=20, blank=True, null=True) 
    email = models.EmailField(unique=True) 
    empresa = models.CharField(max_length=100, blank=True, null=True) 
 
    estado = models.CharField(
        max_length=50,
        choices=[
            ('activo', 'Activo'),
            ('inactivo', 'Inactivo'),
            ('potencial', 'Potencial')
        ],
        default='potencial'
    )
    ciudad = models.CharField(max_length=100, blank=True, null=True) 
    origen = models.CharField(
        max_length=50,
        choices=[
            ('web', 'Sitio Web'),
            ('whatsapp', 'WhatsApp Directo'),
            ('redes', 'Redes Sociales'),
            ('referido', 'Referido'),
            ('otro', 'Otro')
        ],
        default='otro'
    )
    fecha_registro = models.DateField(auto_now_add=True) 
    notas = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f"{self.nombre} ({self.email})" 
