from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from proyectos.models import Proyecto
from cotizaciones.models import Cotizacion
from clientes.models import Cliente

class InformeGerencialView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # informe de cotizacione
        total_cotizaciones = Cotizacion.objects.count()
        aceptadas = Cotizacion.objects.filter(estado='aceptada').count()
        tasa_conversion = (aceptadas / total_cotizaciones * 100) if total_cotizaciones > 0 else 0

        # Rendimiento financiero
        ingresos_por_tipo = Proyecto.objects.filter(
            cotizaciones__estado='aceptada'
        ).values('tipo_evento').annotate(
            total_generado=Sum('cotizaciones__total'),
            cantidad_proyectos=Count('id')
        ).order_by('-total_generado')

        # Clientes mas valiosos
        clientes_top = Cliente.objects.annotate(
            total_invertido=Sum('proyectos__cotizaciones__total')
        ).filter(proyectos__cotizaciones__estado='aceptada').values('nombre', 'total_invertido').order_by('-total_invertido')[:5]

        reporte = {
            "resumen_conversion": {
                "total": total_cotizaciones,
                "aceptadas": aceptadas,
                "tasa_exito_porcentaje": round(tasa_conversion, 2)
            },
            "ingresos_por_tipo_evento": ingresos_por_tipo,
            "top_5_clientes": clientes_top
        }

        return Response(reporte)