from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CRMUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields["role"] = "admin"
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    objects = CRMUserManager()

    ROLE_CHOICES = (
        ('admin', 'Administrador'),
        ('sales', 'Ventas'),
        ('production', 'Producción'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='sales'
    )

    # is_active ya viene en AbstractUser
    # username, email, password tambien

    def __str__(self):
        return f"{self.username} ({self.role})"
