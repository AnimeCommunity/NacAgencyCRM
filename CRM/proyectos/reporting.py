from django.db.models import Count, DecimalField, OuterRef, Q, Subquery, Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

from clientes.models import Cliente
from cotizaciones.models import Cotizacion
from interacciones.models import Interaccion
from proyectos.models import Proyecto


def _parse_date_param(params, name):
    raw = params.get(name)
    if not raw:
        return None
    value = parse_date(raw)
    if value is None:
        raise ValidationError({name: "Usa el formato de fecha AAAA-MM-DD."})
    return value


def _parse_int_param(params, name):
    raw = params.get(name)
    if not raw:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError({name: "Debe ser un identificador numérico."}) from exc


def parse_report_filters(params):
    desde = _parse_date_param(params, "desde")
    hasta = _parse_date_param(params, "hasta")
    if desde and hasta and desde > hasta:
        raise ValidationError({"periodo": "La fecha inicial no puede ser posterior a la final."})
    return {
        "desde": desde,
        "hasta": hasta,
        "cliente": _parse_int_param(params, "cliente"),
        "responsable": _parse_int_param(params, "responsable"),
        "estado_proyecto": params.get("estado_proyecto") or None,
        "tipo_evento": params.get("tipo_evento") or None,
    }


def get_report_querysets(filters):
    clients = Cliente.objects.all()
    projects = Proyecto.objects.select_related("cliente", "responsable")
    quotations = Cotizacion.objects.select_related(
        "projecto", "projecto__cliente", "projecto__responsable"
    ).prefetch_related("items")
    interactions = Interaccion.objects.select_related("cliente", "created_by")

    desde = filters["desde"]
    hasta = filters["hasta"]
    if desde:
        projects = projects.filter(fecha_inicio__gte=desde)
        quotations = quotations.filter(created_at__gte=desde)
        interactions = interactions.filter(created_at__date__gte=desde)
    if hasta:
        projects = projects.filter(fecha_inicio__lte=hasta)
        quotations = quotations.filter(created_at__lte=hasta)
        interactions = interactions.filter(created_at__date__lte=hasta)

    cliente_id = filters["cliente"]
    if cliente_id:
        clients = clients.filter(id=cliente_id)
        projects = projects.filter(cliente_id=cliente_id)
        quotations = quotations.filter(projecto__cliente_id=cliente_id)
        interactions = interactions.filter(cliente_id=cliente_id)

    responsable_id = filters["responsable"]
    if responsable_id:
        projects = projects.filter(responsable_id=responsable_id)
        quotations = quotations.filter(projecto__responsable_id=responsable_id)
        interactions = interactions.filter(created_by_id=responsable_id)

    estado_proyecto = filters["estado_proyecto"]
    if estado_proyecto:
        projects = projects.filter(estado=estado_proyecto)
        quotations = quotations.filter(projecto__estado=estado_proyecto)

    tipo_evento = filters["tipo_evento"]
    if tipo_evento:
        projects = projects.filter(tipo_evento=tipo_evento)
        quotations = quotations.filter(projecto__tipo_evento=tipo_evento)

    if estado_proyecto or tipo_evento:
        interactions = interactions.filter(
            cliente_id__in=projects.values("cliente_id")
        )

    if any(filters.values()):
        cohort_client_ids = set(projects.values_list("cliente_id", flat=True))
        cohort_client_ids.update(
            quotations.values_list("projecto__cliente_id", flat=True)
        )
        cohort_client_ids.update(interactions.values_list("cliente_id", flat=True))
        clients = clients.filter(id__in=cohort_client_ids)

    return {
        "clients": clients.order_by("nombre"),
        "projects": projects.order_by("fecha_inicio", "nombre"),
        "quotations": quotations.order_by("-created_at", "-id"),
        "interactions": interactions.order_by("-created_at"),
    }


def _percentage(numerator, denominator):
    return round(numerator / denominator * 100, 2) if denominator else 0


def _status_counts(queryset):
    return list(
        queryset.order_by()
        .values("estado")
        .annotate(total=Count("id"))
        .order_by("estado")
    )


def _activity_rows(querysets, trunc_function, label_format):
    buckets = {}

    for row in (
        querysets["projects"].order_by()
        .annotate(periodo=trunc_function("fecha_inicio"))
        .values("periodo")
        .annotate(total=Count("id"))
    ):
        key = row["periodo"].strftime(label_format)
        buckets.setdefault(key, {"periodo": key, "proyectos": 0, "cotizaciones": 0, "interacciones": 0, "ingresos_aceptados": 0})
        buckets[key]["proyectos"] = row["total"]

    for row in (
        querysets["quotations"].order_by()
        .annotate(periodo=trunc_function("created_at"))
        .values("periodo")
        .annotate(
            cantidad=Count("id"),
            ingresos_aceptados=Sum("total", filter=Q(estado="aceptada")),
        )
    ):
        key = row["periodo"].strftime(label_format)
        buckets.setdefault(key, {"periodo": key, "proyectos": 0, "cotizaciones": 0, "interacciones": 0, "ingresos_aceptados": 0})
        buckets[key]["cotizaciones"] = row["cantidad"]
        buckets[key]["ingresos_aceptados"] = row["ingresos_aceptados"] or 0

    for row in (
        querysets["interactions"].order_by()
        .annotate(periodo=trunc_function("created_at"))
        .values("periodo")
        .annotate(total=Count("id"))
    ):
        key = row["periodo"].strftime(label_format)
        buckets.setdefault(key, {"periodo": key, "proyectos": 0, "cotizaciones": 0, "interacciones": 0, "ingresos_aceptados": 0})
        buckets[key]["interacciones"] = row["total"]

    return [buckets[key] for key in sorted(buckets)]


def build_management_report(params):
    filters = parse_report_filters(params)
    querysets = get_report_querysets(filters)
    clients = querysets["clients"]
    projects = querysets["projects"]
    quotations = querysets["quotations"]
    interactions = querysets["interactions"]

    total_quotations = quotations.count()
    accepted = quotations.filter(estado="aceptada").count()
    pending = quotations.filter(estado="enviada").count()
    rejected = quotations.filter(estado="rechazada").count()
    expired = quotations.filter(estado="vencida").count()

    quote_clients = quotations.order_by().values("projecto__cliente_id").distinct().count()
    closed_clients = (
        quotations.filter(estado="aceptada").order_by()
        .values("projecto__cliente_id")
        .distinct()
        .count()
    )
    payment_projects = Proyecto.objects.select_related("cliente", "responsable").filter(
        pagado=True,
        cliente_id__in=quotations.filter(estado="aceptada").values(
            "projecto__cliente_id"
        ),
    )
    if filters["desde"]:
        payment_projects = payment_projects.filter(fecha_pago__gte=filters["desde"])
    if filters["hasta"]:
        payment_projects = payment_projects.filter(fecha_pago__lte=filters["hasta"])
    if filters["cliente"]:
        payment_projects = payment_projects.filter(cliente_id=filters["cliente"])
    if filters["responsable"]:
        payment_projects = payment_projects.filter(responsable_id=filters["responsable"])
    if filters["estado_proyecto"]:
        payment_projects = payment_projects.filter(estado=filters["estado_proyecto"])
    if filters["tipo_evento"]:
        payment_projects = payment_projects.filter(tipo_evento=filters["tipo_evento"])
    payment_projects = payment_projects.filter(
        id__in=quotations.filter(estado="aceptada").values("projecto_id")
    )
    paid_clients = (
        payment_projects.order_by().values("cliente_id").distinct().count()
    )
    total_clients = clients.count()

    accepted_quotes = quotations.filter(estado="aceptada").order_by()
    accepted_revenue = accepted_quotes.aggregate(total=Sum("total"))["total"] or 0
    latest_accepted_total = (
        accepted_quotes.filter(projecto_id=OuterRef("pk"))
        .order_by("-created_at", "-id")
        .values("total")[:1]
    )
    paid_revenue = (
        payment_projects.annotate(
            accepted_total=Subquery(
                latest_accepted_total,
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        ).aggregate(total=Sum("accepted_total"))["total"]
        or 0
    )

    income_by_type = list(
        accepted_quotes.values("projecto__tipo_evento")
        .annotate(
            total_generado=Sum("total"),
            cantidad_proyectos=Count("projecto_id", distinct=True),
        )
        .order_by("-total_generado")
    )
    income_by_type = [
        {
            "tipo_evento": row["projecto__tipo_evento"],
            "total_generado": row["total_generado"],
            "cantidad_proyectos": row["cantidad_proyectos"],
        }
        for row in income_by_type
    ]

    top_clients = list(
        accepted_quotes.values("projecto__cliente__nombre")
        .annotate(total_invertido=Sum("total"))
        .order_by("-total_invertido")[:5]
    )
    top_clients = [
        {"nombre": row["projecto__cliente__nombre"], "total_invertido": row["total_invertido"]}
        for row in top_clients
    ]

    quotation_counts = {
        row["projecto_id"]: row
        for row in quotations.order_by()
        .values("projecto_id")
        .annotate(
            cotizaciones_total=Count("id"),
            cotizaciones_aceptadas=Count("id", filter=Q(estado="aceptada")),
        )
    }
    clients_by_project = [
        {
            "proyecto_id": row["id"],
            "proyecto_nombre": row["nombre"],
            "estado": row["estado"],
            "pagado": row["pagado"],
            "cliente_id": row["cliente_id"],
            "cliente_nombre": row["cliente__nombre"],
            "cotizaciones": quotation_counts.get(row["id"], {}).get(
                "cotizaciones_total", 0
            ),
            "cotizaciones_aceptadas": quotation_counts.get(row["id"], {}).get(
                "cotizaciones_aceptadas", 0
            ),
        }
        for row in projects.order_by().values(
            "id",
            "nombre",
            "estado",
            "pagado",
            "cliente_id",
            "cliente__nombre",
        )
    ]

    payload = {
        "filtros": {
            key: value.isoformat() if hasattr(value, "isoformat") else value
            for key, value in filters.items()
        },
        "resumen_conversion": {
            "total": total_quotations,
            "aceptadas": accepted,
            "pendientes": pending,
            "rechazadas": rejected,
            "vencidas": expired,
            "tasa_exito_porcentaje": _percentage(accepted, total_quotations),
        },
        "clientes_conversion": {
            "total_clientes": total_clients,
            "clientes_que_cotizaron": quote_clients,
            "clientes_que_concretaron": closed_clients,
            "clientes_que_pagaron": paid_clients,
            "tasa_cliente_a_cotizacion": _percentage(quote_clients, total_clients),
            "tasa_cotizacion_a_cierre": _percentage(closed_clients, quote_clients),
            "tasa_cierre_a_pago": _percentage(paid_clients, closed_clients),
        },
        "resumen_financiero": {
            "ingresos_aceptados": accepted_revenue,
            "ingresos_pagados": paid_revenue,
            "saldo_por_cobrar": accepted_revenue - paid_revenue,
        },
        "clientes_por_estado": _status_counts(clients),
        "proyectos_por_estado": _status_counts(projects),
        "cotizaciones_por_estado": _status_counts(quotations),
        "interacciones_por_resultado": list(
            interactions.values("resultado")
            .annotate(total=Count("id"))
            .order_by("-total", "resultado")
        ),
        "ingresos_por_tipo_evento": income_by_type,
        "top_5_clientes": top_clients,
        "clientes_por_proyecto": clients_by_project,
        "actividad_mensual": _activity_rows(querysets, TruncMonth, "%Y-%m"),
        "actividad_semanal": _activity_rows(querysets, TruncWeek, "%Y-%m-%d"),
    }
    return payload, querysets
