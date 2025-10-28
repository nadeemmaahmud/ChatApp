from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, StripeWebhookView

router = DefaultRouter()
router.register(r'subscription', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]