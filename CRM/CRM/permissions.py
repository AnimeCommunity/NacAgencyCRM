from rest_framework.permissions import BasePermission, SAFE_METHODS

class RolePermission(BasePermission):
    """
    Permisos simples basados en rol
    """

    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        # Admin puede todo
        if user.role == 'admin':
            return True

        # Métodos de solo lectura
        if request.method in SAFE_METHODS:
            return True

        # Reglas por rol
        if user.role == 'ventas':
            return self.allow_sales(view)

        if user.role == 'produccion':
            return self.allow_production(view)

        return False

    def allow_sales(self, view):
        # Ventas no puede tocar usuarios
        return view.basename not in ['users']

    def allow_production(self, view):
        # Producción solo lectura excepto interacciones
        return view.basename in ['interactions']
