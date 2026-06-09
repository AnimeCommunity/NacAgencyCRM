# crm/urls.py (Tu archivo principal unificado)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from clientes.views import ClientViewSet
from proyectos.views import ProjectViewSet
from cotizaciones.views import QuotationViewSet
from interacciones.views import InteractionViewSet
from marketing.views import PlantillaMensajeViewSet, ConfigSMTPViewSet
from proyectos.reports_views import InformeGerencialView # 👈 Importamos tu vista de reportes

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'quotations', QuotationViewSet)
router.register(r'interactions', InteractionViewSet)
router.register(r'marketing-templates', PlantillaMensajeViewSet)
router.register(r'marketing-config', ConfigSMTPViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('marketing/', include('marketing.urls')), 
    
    # ruta para el informe 
    path('reports/gerencial/', InformeGerencialView.as_view(), name='informe-gerencial'),
]