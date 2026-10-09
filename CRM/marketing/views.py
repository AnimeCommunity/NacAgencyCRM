import logging
import urllib.parse

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count, Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from CRM.permissions import RolePermission
from clientes.models import Cliente
from cotizaciones.models import Cotizacion
from interacciones.models import Interaccion
from proyectos.models import Proyecto
from .models import ConfigSMTP, PlantillaMensaje
from .serializers import ConfigSMTPSerializer, PlantillaMensajeSerializer
from .smtp_secrets import SMTPSecretError, decrypt_smtp_password
from .utils import exportar_clientes_excel


logger = logging.getLogger(__name__)


def _smtp_password(config):
    if config.email_password:
        return decrypt_smtp_password(config.email_password)
    return getattr(settings, "CRM_SMTP_PASSWORD", "")


def _smtp_connection(config):
    allowed_hosts = set(getattr(settings, "CRM_SMTP_ALLOWED_HOSTS", []))
    if config.servidor_host not in allowed_hosts:
        raise ValueError("El servidor SMTP no está permitido por la configuración.")
    password = _smtp_password(config)
    if not password:
        raise ValueError("La contraseña SMTP no está configurada.")
    return get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host=config.servidor_host,
        port=config.puerto,
        username=config.email_usuario,
        password=password,
        use_tls=config.use_tls,
        timeout=10,
    )


class PlantillaMensajeViewSet(ModelViewSet):
    queryset = PlantillaMensaje.objects.all().order_by("-created_at")
    serializer_class = PlantillaMensajeSerializer
    permission_classes = [RolePermission]
    role_permissions = {
        "list": {"sales", "production"},
        "retrieve": {"sales", "production"},
        "create": {"sales"},
        "update": {"sales"},
        "partial_update": {"sales"},
        "destroy": {"sales"},
    }


class ConfigSMTPViewSet(ModelViewSet):
    queryset = ConfigSMTP.objects.all()
    serializer_class = ConfigSMTPSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": {"admin"}}

    @action(detail=True, methods=["post"], url_path="test-connection")
    def test_connection(self, request, pk=None):
        config = self.get_object()
        try:
            connection = _smtp_connection(config)
            connection.open()
            connection.close()
        except (ValueError, SMTPSecretError, ImproperlyConfigured) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("No fue posible verificar la conexión SMTP")
            return Response(
                {"error": "No fue posible conectar con el servidor SMTP."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({"status": "Conexión SMTP verificada."})


class EnviarCampanaView(APIView):
    permission_classes = [RolePermission]
    role_permissions = {"POST": {"sales"}}

    def post(self, request):
        try:
            cliente = Cliente.objects.get(id=request.data.get("cliente_id"))
            plantilla = PlantillaMensaje.objects.get(id=request.data.get("plantilla_id"))
        except (Cliente.DoesNotExist, PlantillaMensaje.DoesNotExist):
            return Response({"error": "Cliente o plantilla no encontrados."}, status=404)

        try:
            body = plantilla.contenido.format(nombre=cliente.nombre)
        except (KeyError, ValueError):
            return Response(
                {"error": "La plantilla contiene variables no compatibles."}, status=400
            )

        if plantilla.tipo == "email":
            return self._send_email(request, cliente, plantilla, body)
        if plantilla.tipo == "whatsapp":
            return self._create_whatsapp_link(request, cliente, body)
        return Response({"error": "Tipo de plantilla no soportado."}, status=400)

    def _send_email(self, request, cliente, plantilla, body):
        config = ConfigSMTP.objects.first()
        if not config:
            return Response({"error": "No existe configuración SMTP."}, status=400)

        try:
            connection = _smtp_connection(config)
            email = EmailMessage(
                subject=plantilla.asunto or plantilla.nombre,
                body=body,
                from_email=config.email_usuario,
                to=[cliente.email],
                connection=connection,
            )
            email.send(fail_silently=False)
        except (ValueError, SMTPSecretError, ImproperlyConfigured) as exc:
            return Response({"error": str(exc)}, status=400)
        except Exception:
            logger.exception("No fue posible enviar la campaña SMTP")
            return Response(
                {"error": "No fue posible enviar el correo. Revisa la configuración SMTP."},
                status=502,
            )

        Interaccion.objects.create(
            cliente=cliente,
            tipo="email_marketing",
            descripcion=f"Asunto: {plantilla.asunto or plantilla.nombre}\n\n{body}",
            created_by=request.user,
        )
        return Response({"status": "Email enviado e indexado con éxito."})

    @staticmethod
    def _create_whatsapp_link(request, cliente, body):
        if not cliente.telefono:
            return Response({"error": "El cliente no tiene teléfono registrado."}, status=400)
        telefono = "".join(filter(str.isdigit, cliente.telefono))
        if not telefono:
            return Response({"error": "El teléfono no es válido."}, status=400)

        whatsapp_url = f"https://wa.me/{telefono}?text={urllib.parse.quote(body)}"
        Interaccion.objects.create(
            cliente=cliente,
            tipo="whatsapp_link",
            descripcion=f"Se generó un enlace de WhatsApp con el mensaje: {body}",
            created_by=request.user,
        )
        return Response({"status": "URL generada", "url": whatsapp_url})


class DashboardStatsView(APIView):
    permission_classes = [RolePermission]
    role_permissions = {"GET": {"sales", "production"}}

    def get(self, request):
        origenes = (
            Cliente.objects.values("origen")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        ejecutivos = (
            Cotizacion.objects.filter(estado="enviada")
            .values("projecto__responsable__username")
            .annotate(total_cotizaciones=Count("id"), monto_proyectado=Sum("total"))
        )
        ventas_totales = Proyecto.objects.filter(estado="finalizado").aggregate(
            total_ingresos=Sum("presupuesto_estimado"), cantidad_ventas=Count("id")
        )
        return Response(
            {
                "origenes": origenes,
                "ejecutivos": ejecutivos,
                "resumen_ventas": {
                    "total_ingresos": ventas_totales["total_ingresos"] or 0,
                    "cantidad_ventas": ventas_totales["cantidad_ventas"] or 0,
                },
            }
        )


class ExportarExcelView(APIView):
    permission_classes = [RolePermission]
    role_permissions = {"GET": {"sales"}}

    def get(self, request):
        return exportar_clientes_excel(Cliente.objects.all().order_by("nombre"))
