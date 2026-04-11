from django.urls import path, include
from rest_framework.routers import DefaultRouter 
from .views import InteraccionViewSet # Importa la vista InteraccionViewSet

# Configura el enrutador por defecto y registra la vista InteraccionViewSet
router = DefaultRouter()
router.register(r'', InteraccionViewSet) # Registra la vista InteraccionViewSet

urlpatterns = [
    path('', include(router.urls)), # Incluye las URLs generadas por el enrutador
]
