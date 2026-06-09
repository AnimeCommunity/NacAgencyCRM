from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

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
