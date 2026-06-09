# marketing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlantillaMensajeViewSet, ConfigSMTPViewSet, EnviarCampanaView, DashboardStatsView, ExportarExcelView

router = DefaultRouter()
router.register(r'templates', PlantillaMensajeViewSet)
router.register(r'config-smtp', ConfigSMTPViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('enviar-campana/', EnviarCampanaView.as_view(), name='enviar-campana'),
    
    
    path('stats/', DashboardStatsView.as_view(), name='marketing-stats'),
    path('export-excel/', ExportarExcelView.as_view(), name='export-clientes-excel'),
]