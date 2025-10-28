from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from .serializers import (
    CustomUserSerializer, 
    ChangePasswordSerializer, 
    ForgotPasswordSerializer, 
    ResetPasswordSerializer,
    UpdateProfileSerializer
)
from .permissions import IsAdminUserOrOthers
from .utils import send_verification_email, send_password_reset_email
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        elif self.action == "list":
            return [permissions.IsAdminUser()]
        elif self.action in ["send_verification", "me", "change_password", "update_profile"]:
            return [permissions.IsAuthenticated()]
        elif self.action in ["verify", "forgot_password", "reset_password"]:
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

    @action(detail=False, methods=["put", "patch"], url_path="update-profile")
    def update_profile(self, request):
        user = request.user
        old_email = user.email
        serializer = UpdateProfileSerializer(user, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        updated_user = serializer.save()
        
        if updated_user.email != old_email:
            updated_user.is_verified = False
            updated_user.save(update_fields=["is_verified"])
            send_verification_email(updated_user)
            updated_user.refresh_from_db()
            response_data = {
                "user": CustomUserSerializer(updated_user).data,
                "detail": "Profile updated successfully. Please verify your new email address."
            }
        else:
            response_data = {
                "user": CustomUserSerializer(updated_user).data,
                "detail": "Profile updated successfully."
            }
        
        return Response(response_data, status=status.HTTP_200_OK)

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

    @action(detail=False, methods=["post"], url_path="change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="forgot-password")
    def forgot_password(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                success = send_password_reset_email(user)
                if success:
                    return Response(
                        {"detail": "Password reset email sent successfully"}, 
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"detail": "Failed to send password reset email"}, 
                        status=status.HTTP_502_BAD_GATEWAY
                    )
            except CustomUser.DoesNotExist:
                return Response(
                    {"detail": "If an account with this email exists, a password reset link has been sent"}, 
                    status=status.HTTP_200_OK
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="reset-password")
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token_value = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                token = PasswordResetToken.objects.select_related("user").get(token=token_value)
            except PasswordResetToken.DoesNotExist:
                return Response({"detail": "Invalid reset token"}, status=status.HTTP_400_BAD_REQUEST)
            
            if token.is_expired:
                token.delete()
                return Response({"detail": "Reset token has expired"}, status=status.HTTP_400_BAD_REQUEST)
            
            user = token.user
            user.set_password(new_password)
            user.save()
            
            PasswordResetToken.objects.filter(user=user).delete()
            
            return Response({"detail": "Password reset successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)