from rest_framework.permissions import BasePermission


class IsAthlete(BasePermission):
    message = "An athlete account is required."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == "athlete")
