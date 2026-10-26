from rest_framework.permissions import BasePermission


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == "ADMIN")


class AdministratorOnly(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)


class DomainPermission(BasePermission):
    """Views declare read/write roles; object querysets must enforce branch scope."""
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        if is_admin(user):
            return True
        roles = getattr(view, "read_roles", ()) if request.method in ("GET", "HEAD", "OPTIONS") else getattr(view, "write_roles", ())
        return user.role in roles
