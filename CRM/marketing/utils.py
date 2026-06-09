import openpyxl
from django.http import HttpResponse

def exportar_clientes_excel(queryset):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte de Clientes"

    # Cabeceras
    columns = ['Nombre', 'Email', 'Teléfono', 'Origen', 'Fecha Registro']
    ws.append(columns)

    for objeto in queryset:
        ws.append([objeto.nombre, objeto.email, objeto.telefono, objeto.origen, objeto.fecha_registro.replace(tzinfo=None)])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=reporte_clientes.xlsx'
    wb.save(response)
    return response