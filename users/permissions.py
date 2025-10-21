from rest_framework import permissions

class IsAdminUserOrOthers(permissions.BasePermission):
     def has_permission(self, request, view):
        if not request.user.is_authenticated and request.method == "POST":
            return True
        elif request.user.is_authenticated and request.user.is_staff and request.method in ['GET', 'PUT', 'DELETE']:
            return True
        return False