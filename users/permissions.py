from rest_framework import permissions

class IsAdminUserOrOthers(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "POST":
            return True

        if request.user and request.user.is_authenticated:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True

        return obj == request.user