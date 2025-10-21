from rest_framework.viewsets import ModelViewSet
from .models import CustomUser
from .serializers import CustomUserSerializer
from .permissions import IsAdminUserOrOthers

class CustomUserViewSet(ModelViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [IsAdminUserOrOthers]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserSerializer
        return CustomUserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "User registered successfully."
            },
            status=status.HTTP_201_CREATED
        )