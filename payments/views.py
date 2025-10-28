from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import stripe
import logging

from .models import SubscriptionPlan, UserSubscription, MessageUsage, Payment
from .serializers import (
    SubscriptionPlanSerializer, 
    UserSubscriptionSerializer, 
    MessageUsageSerializer,
    CreatePaymentIntentSerializer
)

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def status(self, request):
        try:
            subscription = request.user.subscription
            serializer = UserSubscriptionSerializer(subscription)
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response({'error': 'No subscription found'}, status=404)

    @action(detail=False, methods=['get'])
    def usage(self, request):
        try:
            usage = request.user.message_usage
            serializer = MessageUsageSerializer(usage)
            return Response(serializer.data)
        except MessageUsage.DoesNotExist:
            return Response({'error': 'No usage data found'}, status=404)

    @action(detail=False, methods=['get'])
    def upgrade_options(self, request):
        pro_plans = SubscriptionPlan.objects.filter(plan_type='pro', is_active=True)
        serializer = SubscriptionPlanSerializer(pro_plans, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        serializer = CreatePaymentIntentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'])
            
            payment_intent = stripe.PaymentIntent.create(
                amount=int(plan.price * 100),
                currency='usd',
                metadata={
                    'user_id': str(request.user.id),
                    'user_email': request.user.email,
                    'plan_id': str(plan.id),
                    'plan_name': plan.name,
                }
            )

            payment = Payment.objects.create(
                user=request.user,
                stripe_payment_intent_id=payment_intent.id,
                amount=plan.price,
                plan=plan
            )

            return Response({
                'client_secret': payment_intent.client_secret,
                'payment_id': payment.id,
                'amount': plan.price,
                'plan_name': plan.name,
            })

        except Exception as e:
            return Response({'error': 'Payment creation failed'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    permission_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except:
            return HttpResponse('Invalid signature', status=400)

        if event['type'] == 'payment_intent.succeeded':
            self._handle_payment_success(event['data']['object'])

        return HttpResponse(status=200)

    def _handle_payment_success(self, payment_intent):
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            payment.status = 'completed'
            payment.save()
            
            user_subscription = payment.user.subscription
            user_subscription.plan = payment.plan
            user_subscription.status = 'active'
            user_subscription.end_date = None
            user_subscription.save()
            
            if payment.plan.duration_days > 0:
                from django.utils import timezone
                from datetime import timedelta
                user_subscription.end_date = timezone.now() + timedelta(days=payment.plan.duration_days)
                user_subscription.save()
            
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for intent {payment_intent['id']}")