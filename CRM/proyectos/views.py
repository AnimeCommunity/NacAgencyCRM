from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db import transaction
from django.shortcuts import get_object_or_404

from CRM.permissions import RolePermission
from .models import Proyecto
from .serializers import ProjectDetailSerializer, ProjectSerializer


class ProjectViewSet(ModelViewSet):
    queryset = Proyecto.objects.select_related("cliente", "responsable")
    permission_classes = [RolePermission]
    role_permissions = {
        "list": {"sales", "production"},
        "retrieve": {"sales", "production"},
        "create": {"sales"},
        "update": {"sales"},
        "partial_update": {"sales"},
        "destroy": set(),
        "cancel": {"sales"},
    }

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ProjectDetailSerializer
        return ProjectSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        with transaction.atomic():
            project = get_object_or_404(
                Proyecto.objects.select_for_update(), pk=kwargs["pk"]
            )
            self.check_object_permissions(request, project)
            serializer = self.get_serializer(
                project, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        with transaction.atomic():
            project = get_object_or_404(
                Proyecto.objects.select_for_update(), pk=pk
            )
            self.check_object_permissions(request, project)
            if project.estado == "finalizado":
                return Response(
                    {"estado": "Un proyecto finalizado no puede cancelarse."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if project.estado != "cancelado":
                project.estado = "cancelado"
                project.save(update_fields=["estado"])
        return Response(ProjectDetailSerializer(project).data)
