from django.db import models

# Create your models here.
class Cotizacion(models.Model):
    projecto = models.ForeignKey('proyectos.Proyecto', on_delete=models.CASCADE, related_name='cotizaciones')  # Relacion con el proyecto
    numero = models.CharField(max_length=50, unique=True)  #serial o numero de la cotizacion
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)  # subtotal sin impuestos
    impuestos = models.DecimalField(max_digits=10, decimal_places=2)  # impuestos aplicados
    total = models.DecimalField(max_digits=10, decimal_places=2)  # monto
    estado = models.CharField(
        max_length=50,
        choices=[
            ('enviada', 'Enviada'),
            ('aceptada', 'Aceptada'),
            ('rechazada', 'Rechazada'),
            ('vencida', 'Vencida')],
        default='enviada')
    fecha_emision = models.DateField(auto_now_add=True)  # fecha de emision
    fecha_vencimiento = models.DateField()  # fecha de vencimiento
    notas = models.TextField(blank=True, null=True)  # notas adicionales


class CotizacionItem(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')  # Relacion con la cotizacion
    descripcion = models.CharField(max_length=200)  # descripcion del item
    cantidad = models.IntegerField()  # cantidad del item
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)  # precio unitario
    total = models.DecimalField(max_digits=10, decimal_places=2)  # total del item (cantidad * precio_unitario)