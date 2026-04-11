from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from clientes.views import ClientViewSet
from proyectos.views import ProjectViewSet
from cotizaciones.views import QuotationViewSet
from interacciones.views import InteractionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'quotations', QuotationViewSet)
router.register(r'interactions', InteractionViewSet)

urlpatterns = router.urls
