from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    """Aplica una matriz de roles definida por cada vista o ViewSet.

    Los administradores siempre tienen acceso. Para los demás roles, la vista
    debe declarar ``role_permissions`` usando acciones de ViewSet (``list``,
    ``create``...) o métodos HTTP como claves.
    """

    message = "No tienes permisos para realizar esta acción."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "role", None) == "admin":
            return True

        permissions = getattr(view, "role_permissions", {})
        action = getattr(view, "action", None)
        allowed_roles = permissions.get(action)
        if allowed_roles is None:
            allowed_roles = permissions.get(request.method)
        if allowed_roles is None:
            allowed_roles = permissions.get("*")

        return allowed_roles is not None and user.role in allowed_roles
