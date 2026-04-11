from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet # Importa la vista ClienteViewSet

# Configura el enrutador por defecto y registra la vista ClienteViewSet
router = DefaultRouter() 
router.register(r'', ClienteViewSet) # Registra la vista ClienteViewSet

urlpatterns = [
    path('', include(router.urls)), # Incluye las URLs generadas por el enrutador
]
