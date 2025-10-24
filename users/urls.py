from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, VerifyEmailAPIView, SendVerificationEmailAPIView, CurrentUserAPIView

router = DefaultRouter()
router.register(r'', CustomUserViewSet, basename='customuser')

urlpatterns = [
    path('', include(router.urls)),
    path('verify/', VerifyEmailAPIView.as_view(), name='users-verify'),
    path('send-verification/', SendVerificationEmailAPIView.as_view(), name='users-send-verification'),
    path('me/', CurrentUserAPIView.as_view(), name='users-current-user'),
]