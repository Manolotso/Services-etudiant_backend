from rest_framework.permissions import BasePermission

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # lecture autorisée pour tous
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # écriture uniquement pour admin
        return request.user.is_authenticated and request.user.role == 'admin'





from rest_framework.permissions import BasePermission

class IsScraperAllowed(BasePermission):
    def has_permission(self, request, view):
        api_key = request.headers.get("X-API-KEY")

        return api_key == "MY_SECRET_KEY_123"