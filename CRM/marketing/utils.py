import openpyxl
from django.http import HttpResponse


DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@")


def safe_excel_value(value):
    if isinstance(value, str) and value.startswith(DANGEROUS_FORMULA_PREFIXES):
        return f"'{value}"
    return value


def exportar_clientes_excel(queryset):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Reporte de Clientes"
    sheet.append(["Nombre", "Email", "Teléfono", "Origen", "Fecha Registro"])

    for cliente in queryset:
        sheet.append(
            [
                safe_excel_value(cliente.nombre),
                safe_excel_value(cliente.email),
                safe_excel_value(cliente.telefono or ""),
                cliente.origen,
                cliente.created_at,
            ]
        )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="reporte_clientes.xlsx"'
    workbook.save(response)
    return response
