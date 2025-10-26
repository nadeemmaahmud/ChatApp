from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser, EmailVerificationToken
from .serializers import CustomUserSerializer
from .permissions import IsAdminUserOrOthers
from .utils import send_verification_email
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        elif self.action == "list":
            return [permissions.IsAdminUser()]
        elif self.action in ["send_verification", "me"]:
            return [permissions.IsAuthenticated()]
        elif self.action == "verify":
            return [permissions.AllowAny()]
        else:
            return [IsAdminUserOrOthers()]
        
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"detail": "Email and password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=email, password=password)
        
        if not user:
            return Response(
                {"detail": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_verified:
            return Response(
                {"detail": "Account not verified"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            "user": self.serializer_class(user).data,
            "access": str(access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        return Response(self.serializer_class(request.user).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="send-verification")
    def send_verification(self, request):
        user = request.user
        if user.is_verified:
            return Response({"detail": "Account already verified"}, status=status.HTTP_400_BAD_REQUEST)
        ok = send_verification_email(user)
        if not ok:
            return Response({"detail": "Failed to send email"}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"detail": "Verification email sent"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get", "post"], url_path="verify")
    def verify(self, request):
        token_value = request.query_params.get("token") or request.data.get("token")
        if not token_value:
            return Response({"detail": "token is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = EmailVerificationToken.objects.select_related("user").get(token=token_value)
        except EmailVerificationToken.DoesNotExist:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        if token.is_expired:
            token.delete()
            return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)
        user = token.user
        if not user.is_verified:
            user.is_verified = True
            user.save(update_fields=["is_verified"])
        EmailVerificationToken.objects.filter(user=user).delete()
        return Response({"detail": "Account verified"}, status=status.HTTP_200_OK)


from rest_framework.views import APIView

class LoginUserView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {"detail": "Email and password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=email, password=password)
        
        if not user:
            return Response(
                {"detail": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified
            },
            "access": str(access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_200_OK)