import stripe
import os
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Plan, Subscription, Payment, MessageUsage
from .serializers import (
    PlanSerializer, SubscriptionSerializer, PaymentSerializer,
    MessageUsageSerializer, CreatePaymentIntentSerializer,
    UserSubscriptionStatusSerializer
)
from django.contrib.auth import get_user_model
import json
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        plan_type = self.request.query_params.get('type', None)
        if plan_type:
            queryset = queryset.filter(plan_type=plan_type)
        return queryset


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        try:
            subscription = request.user.subscription
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            return Response({
                'message': 'No active subscription',
                'subscription': None
            }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        subscription = self.get_object()
        
        if subscription.stripe_subscription_id:
            try:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
            except stripe.error.StripeError as e:
                logger.error(f"Stripe cancellation error: {str(e)}")
                return Response({
                    'error': 'Failed to cancel subscription'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        subscription.status = 'cancelled'
        subscription.is_active = False
        subscription.save()
        
        return Response({
            'message': 'Subscription cancelled successfully'
        })


class CreatePaymentIntentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        if serializer.is_valid():
            plan_id = serializer.validated_data['plan_id']
            plan = Plan.objects.get(id=plan_id)
            
            try:
                intent = stripe.PaymentIntent.create(
                    amount=int(plan.price * 100),
                    currency='usd',
                    metadata={
                        'user_id': request.user.id,
                        'plan_id': plan.id,
                        'email': request.user.email
                    }
                )
                
                payment = Payment.objects.create(
                    user=request.user,
                    plan=plan,
                    stripe_payment_intent_id=intent.id,
                    amount=plan.price,
                    status='pending'
                )
                
                return Response({
                    'client_secret': intent.client_secret,
                    'payment_id': payment.id,
                    'amount': plan.price
                })
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error: {str(e)}")
                return Response({
                    'error': 'Payment processing failed'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageUsageView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        usage, created = MessageUsage.objects.get_or_create(user=request.user)
        serializer = MessageUsageSerializer(usage)
        return Response(serializer.data)


class UserSubscriptionStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        MessageUsage.objects.get_or_create(user=request.user)
        
        serializer = UserSubscriptionStatusSerializer(request.user)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = []
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
        
        if not endpoint_secret:
            logger.error("Stripe webhook secret not configured")
            return HttpResponse(status=400)
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            logger.error("Invalid payload")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature")
            return HttpResponse(status=400)
        
        if event['type'] == 'payment_intent.succeeded':
            self._handle_payment_success(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            self._handle_payment_failure(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            self._handle_subscription_payment_success(event['data']['object'])
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        return HttpResponse(status=200)
    
    def _handle_payment_success(self, payment_intent):
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            payment.status = 'completed'
            payment.save()
            
            subscription, created = Subscription.objects.get_or_create(
                user=payment.user,
                defaults={
                    'plan': payment.plan,
                    'status': 'active',
                    'is_active': True
                }
            )
            
            if not created:
                subscription.plan = payment.plan
                subscription.status = 'active'
                subscription.is_active = True
                subscription.save()
            
            payment.subscription = subscription
            payment.save()
            
            logger.info(f"Payment successful for user {payment.user.email}")
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for intent {payment_intent['id']}")
    
    def _handle_payment_failure(self, payment_intent):
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            payment.status = 'failed'
            payment.save()
            
            logger.info(f"Payment failed for user {payment.user.email}")
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for intent {payment_intent['id']}")
    
    def _handle_subscription_payment_success(self, invoice):
        pass
