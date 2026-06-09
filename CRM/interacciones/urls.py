from django.urls import path, include
from rest_framework.routers import DefaultRouter 
from .views import InteraccionViewSet 


router = DefaultRouter()
router.register(r'', InteraccionViewSet)

urlpatterns = [
    path('', include(router.urls)), 
]
