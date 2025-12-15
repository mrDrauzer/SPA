from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """Разрешение на уровне объекта: доступ только владельцу."""

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'user_id', None) == getattr(request.user, 'id', None)


class IsReadOnly(BasePermission):
    """Разрешает только безопасные методы."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
