from rest_framework.response import Response
from rest_framework.views import APIView

from CRM.permissions import RolePermission
from .report_exports import export_management_report_xlsx
from .reporting import build_management_report


class InformeGerencialView(APIView):
    permission_classes = [RolePermission]
    role_permissions = {"GET": {"sales", "production"}}

    def get(self, request):
        payload, _querysets = build_management_report(request.query_params)
        return Response(payload)


class InformeGerencialExportView(APIView):
    permission_classes = [RolePermission]
    role_permissions = {"GET": {"sales"}}

    def get(self, request):
        payload, querysets = build_management_report(request.query_params)
        return export_management_report_xlsx(payload, querysets)
