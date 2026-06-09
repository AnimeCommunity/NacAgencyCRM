from django.db import models

# Create your models here.
class Cotizacion(models.Model):
    projecto = models.ForeignKey('proyectos.Proyecto', on_delete=models.CASCADE, related_name='cotizaciones') 
    numero = models.CharField(max_length=50, unique=True)  
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  
    impuestos = models.DecimalField(max_digits=10, decimal_places=2) 
    total = models.DecimalField(max_digits=10, decimal_places=2)  
    estado = models.CharField(
        max_length=50,
        choices=[
            ('enviada', 'Enviada'),
            ('aceptada', 'Aceptada'),
            ('rechazada', 'Rechazada'),
            ('vencida', 'Vencida')],
        default='enviada')
    fecha_emision = models.DateField(auto_now_add=True) 
    fecha_vencimiento = models.DateField()  
    notas = models.TextField(blank=True, null=True) 


class CotizacionItem(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')  # Relacion con la cotizacion
    descripcion = models.CharField(max_length=200) 
    cantidad = models.IntegerField()  
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  
    total = models.DecimalField(max_digits=10, decimal_places=2)  