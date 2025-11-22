from django.urls import path
from .views import (
    SubscriptionPlanList,
    MySubscription,
    CreateCheckoutSession,
    stripe_webhook,
    success_view,
    cancel_view
)

urlpatterns = [
    path('plans/', SubscriptionPlanList.as_view(), name='subscription-plans'),
    path('my-subscription/', MySubscription.as_view(), name='my-subscription'),
    path('create-checkout-session/', CreateCheckoutSession.as_view(), name='create-checkout'),
    path('stripe-webhook/', stripe_webhook, name='stripe-webhook'),
    path('success/', success_view, name='payment-success'),
    path('cancel/', cancel_view, name='payment-cancel'),
]