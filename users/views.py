from rest_framework import viewsets, permissions
from .models import CustomUser
from .serializers import CustomUserSerializer
from .permissions import IsAdminUserOrOthers

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        elif self.action == "list":
            return [permissions.IsAdminUser()]
        else:
            return [IsAdminUserOrOthers()]