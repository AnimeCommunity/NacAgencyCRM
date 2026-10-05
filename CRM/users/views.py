from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from CRM.permissions import RolePermission
from .models import User
from .serializers import (
    CRMTokenObtainPairSerializer,
    RegistrationSerializer,
    UserSerializer,
)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [RolePermission]
    role_permissions = {"*": {"admin"}}


class CRMTokenObtainPairView(TokenObtainPairView):
    serializer_class = CRMTokenObtainPairSerializer


class RegisterView(CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_value = request.data.get("refresh")
        if not refresh_value:
            return Response(
                {"refresh": ["Este campo es obligatorio."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_value).blacklist()
        except TokenError:
            return Response(
                {"refresh": ["El token no es válido."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
