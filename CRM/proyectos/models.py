from django.db import models

# Create your models here.
class Proyecto(models.Model):
    cliente = models.ForeignKey('clientes.Cliente', on_delete=models.CASCADE, related_name='proyectos')  # Relacion con el cliente
    nombre = models.CharField(max_length=200)
    descripción = models.TextField()
    tipo_evento = models.CharField(
        max_length=50,
        choices=[
            ('concierto', 'Concierto'),
            ('show', 'Show'),
            ('streaming', 'Streaming'),
            ('fiesta', 'Fiesta'),
            ('sesion_fotografica', 'Sesión Fotográfica'),
            ('otro', 'Otro')
        ],
        default='otro'
    )  # Tipo de evento
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    presupuesto_estimado = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=50,
        choices=[
            ('propuesta', 'Propuesta'),
            ('aprobado', 'Aprobado'),
            ('en_proceso', 'En Proceso'),
            ('finalizado', 'Finalizado'),
            ('cancelado', 'Cancelado')
        ],
        default='propuesta') 
    #responsable 
    created_at = models.DateTimeField(auto_now_add=True)