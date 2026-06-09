from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.mail import get_connection, EmailMessage
import urllib.parse
from django.db.models import Count, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from clientes.models import Cliente
from proyectos.models import Proyecto
from cotizaciones.models import Cotizacion

from interacciones.models import Interaccion
from .models import PlantillaMensaje, ConfigSMTP
from .serializers import PlantillaMensajeSerializer, ConfigSMTPSerializer

# CRUD para las plantillas de mensajes
class PlantillaMensajeViewSet(ModelViewSet):
    queryset = PlantillaMensaje.objects.all()
    serializer_class = PlantillaMensajeSerializer
    permission_classes = [IsAuthenticated]

# CRUD para la configuración SMTP
class ConfigSMTPViewSet(ModelViewSet):
    queryset = ConfigSMTP.objects.all()
    serializer_class = ConfigSMTPSerializer
    permission_classes = [IsAuthenticated]

# endpoint para procesar y disparar los envíos
class EnviarCampanaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cliente_id = request.data.get('cliente_id')
        plantilla_id = request.data.get('plantilla_id')

        try:
            cliente = Cliente.objects.get(id=cliente_id)
            plantilla = PlantillaMensaje.objects.get(id=plantilla_id)
        except (Cliente.DoesNotExist, PlantillaMensaje.DoesNotExist):
            return Response({"error": "Cliente o Plantilla no encontrados"}, status=404)

        cuerpo_personalizado = plantilla.contenido.format(nombre=cliente.nombre)

        # email marketing via SMTP
        if plantilla.tipo == 'email':
            config = ConfigSMTP.objects.first()
            if not config:
                return Response({"error": "No se han configurado los datos de SMTP en el CRM"}, status=400)

            try:
                connection = get_connection(
                    backend='django.core.mail.backends.smtp.EmailBackend',
                    host=config.servidor_host,
                    port=config.puerto,
                    username=config.email_usuario,
                    password=config.email_password,
                    use_tls=config.use_tls
                )
                
                email = EmailMessage(
                    subject=plantilla.asunto,
                    body=cuerpo_personalizado,
                    from_email=config.email_usuario,
                    to=[cliente.email],
                    connection=connection
                )
                email.send()

                # Historial
                Interaccion.objects.create(
                    cliente=cliente,
                    tipo='email_marketing',
                    descripcion=f"Asunto: {plantilla.asunto}\n\nCuerpo:\n{cuerpo_personalizado}",
                    created_by=request.user
                )
                return Response({"status": "Email enviado e indexado con éxito."})
            except Exception as e:
                return Response({"error": f"Error de conexión SMTP: {str(e)}"}, status=500)

        # wasa
        elif plantilla.tipo == 'whatsapp':
            if not cliente.telefono:
                return Response({"error": "El cliente no tiene teléfono registrado"}, status=400)
            
            telefono_limpio = ''.join(filter(str.isdigit, cliente.telefono))
            mensaje_parseado = urllib.parse.quote(cuerpo_personalizado)
            whatsapp_url = f"https://wa.me/{telefono_limpio}?text={mensaje_parseado}"

            # historial
            Interaccion.objects.create(
                cliente=cliente,
                tipo='whatsapp_link',
                descripcion=f"Se generó link de WhatsApp con el mensaje: {cuerpo_personalizado}",
                created_by=request.user
            )
            return Response({"status": "URL generada", "url": whatsapp_url})

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        #  orígenes de clientes
        origenes = Cliente.objects.values('origen').annotate(total=Count('id')).order_by('-total')

        # Cotizaciones activas
        ejecutivos = Cotizacion.objects.filter(estado='enviada').values('projecto__responsable__username').annotate(
            total_cotizaciones=Count('id'),
            monto_proyectado=Sum('total')
        )

        # Ventas realizadas
        ventas_totales = Proyecto.objects.filter(estado='finalizado').aggregate(
            total_ingresos=Sum('presupuesto_estimado'),
            cantidad_ventas=Count('id')
        )

        return Response({
            "origenes": origenes,
            "ejecutivos": ejecutivos,
            "resumen_ventas": {
                "total_ingresos": ventas_totales['total_ingresos'] or 0,
                "cantidad_ventas": ventas_totales['cantidad_ventas'] or 0
            }
        })

class ExportarExcelView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .utils import exportar_clientes_excel
        clientes = Cliente.objects.all()
        return exportar_clientes_excel(clientes)
    def get(self, request):
        origenes = Cliente.objects.values('origen').annotate(total=Count('id')).order_by('-total')

        # cotizaciones activas por ejecutivo
        ejecutivos = Cotizacion.objects.filter(estado='enviada').values('usuario__username').annotate(
            total_cotizaciones=Count('id'),
            monto_proyectado=Sum('total')
        )

        # ventas realizadas
        ventas_totales = Proyecto.objects.filter(estado='finalizado').aggregate(
            total_ingresos=Sum('presupuesto'),
            cantidad_ventas=Count('id')
        )

        return Response({
            "origenes": origenes,
            "ejecutivos": ejecutivos,
            "resumen_ventas": ventas_totales
        })