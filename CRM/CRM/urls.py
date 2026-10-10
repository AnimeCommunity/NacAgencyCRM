from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from clientes.views import ClienteViewSet
from cotizaciones.views import QuotationViewSet
from interacciones.views import InteractionViewSet
from marketing.views import ConfigSMTPViewSet, PlantillaMensajeViewSet
from proyectos.reports_views import InformeGerencialExportView, InformeGerencialView
from proyectos.views import ProjectViewSet
from users.views import CRMTokenObtainPairView, LogoutView, RegisterView, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"clients", ClienteViewSet)
router.register(r"projects", ProjectViewSet)
router.register(r"quotations", QuotationViewSet)
router.register(r"interactions", InteractionViewSet)
router.register(r"marketing-templates", PlantillaMensajeViewSet)
router.register(r"marketing-config", ConfigSMTPViewSet)

urlpatterns = [
    path("api/token/", CRMTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/", include(router.urls)),
    path("api/marketing/", include("marketing.urls")),
    path(
        "api/reports/gerencial/",
        InformeGerencialView.as_view(),
        name="informe-gerencial",
    ),
    path(
        "api/reports/gerencial/export/",
        InformeGerencialExportView.as_view(),
        name="informe-gerencial-export",
    ),
]
