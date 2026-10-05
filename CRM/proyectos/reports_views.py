from django.db.models import Count, Q, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from CRM.permissions import RolePermission
from clientes.models import Cliente
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto


class InformeGerencialView(APIView):
    permission_classes = [RolePermission]
    role_permissions = {"GET": {"sales", "production"}}

    def get(self, request):
        total_cotizaciones = Cotizacion.objects.count()
        aceptadas = Cotizacion.objects.filter(estado="aceptada").count()
        pendientes = Cotizacion.objects.filter(estado="enviada").count()
        tasa_conversion = (
            aceptadas / total_cotizaciones * 100 if total_cotizaciones else 0
        )

        ingresos_por_tipo = (
            Proyecto.objects.values("tipo_evento")
            .annotate(
                total_generado=Sum(
                    "cotizaciones__total",
                    filter=Q(cotizaciones__estado="aceptada"),
                ),
                cantidad_proyectos=Count(
                    "id",
                    filter=Q(cotizaciones__estado="aceptada"),
                    distinct=True,
                ),
            )
            .filter(total_generado__isnull=False)
            .order_by("-total_generado")
        )

        clientes_top = (
            Cliente.objects.annotate(
                total_invertido=Sum(
                    "proyectos__cotizaciones__total",
                    filter=Q(proyectos__cotizaciones__estado="aceptada"),
                )
            )
            .filter(total_invertido__isnull=False)
            .values("nombre", "total_invertido")
            .order_by("-total_invertido")[:5]
        )

        return Response(
            {
                "resumen_conversion": {
                    "total": total_cotizaciones,
                    "aceptadas": aceptadas,
                    "pendientes": pendientes,
                    "tasa_exito_porcentaje": round(tasa_conversion, 2),
                },
                "ingresos_por_tipo_evento": ingresos_por_tipo,
                "top_5_clientes": clientes_top,
            }
        )
