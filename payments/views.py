import stripe
import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SubscriptionPlan, UserSubscription, Payment, MessageUsage
from .serializers import (
    CreateCheckoutSessionSerializer,
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    PaymentSerializer,
    MessageUsageSerializer
)

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionPlanList(APIView):
    """List all active subscription plans"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MySubscription(APIView):
    """Get current user's subscription information"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            subscription = UserSubscription.objects.filter(
                user=request.user
            ).select_related('plan').first()
            
            if not subscription:
                return Response({
                    'message': 'No subscription found',
                    'has_subscription': False,
                    'plan': None,
                    'message_usage': None
                }, status=status.HTTP_200_OK)
            
            message_usage, _ = MessageUsage.objects.get_or_create(user=request.user)
            
            subscription_data = UserSubscriptionSerializer(subscription).data
            message_usage_data = MessageUsageSerializer(message_usage).data
            
            return Response({
                'has_subscription': True,
                'subscription': subscription_data,
                'message_usage': message_usage_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching subscription for user {request.user.email}: {str(e)}")
            return Response(
                {'error': 'Failed to fetch subscription information'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateCheckoutSession(APIView):
    """Create a Stripe checkout session for subscription purchase"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plan_id = serializer.validated_data.get('plan_id')
            
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {'error': 'Invalid or inactive subscription plan'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(plan.price * 100),
                        'product_data': {
                            'name': plan.name,
                            'description': f'{plan.get_plan_type_display()} - {plan.duration_days} days',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{settings.SITE_URL}/payment/success/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.SITE_URL}/payment/cancel/",
                customer_email=request.user.email,
                metadata={
                    'user_id': str(request.user.id),
                    'plan_id': str(plan.id),
                    'user_email': request.user.email,
                }
            )
            
            logger.info(f"Checkout session created for user {request.user.email}, plan {plan.name}")
            
            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return Response(
                {'error': 'Failed to create checkout session'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.warning("Missing Stripe signature header")
        return JsonResponse({'error': 'Missing signature'}, status=400)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    event_type = event['type']
    
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)
    elif event_type == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        logger.info(f"Payment intent succeeded: {payment_intent['id']}")
    elif event_type == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_failed(payment_intent)
    else:
        logger.info(f"Unhandled event type: {event_type}")
    
    return JsonResponse({'status': 'success'}, status=200)

def handle_checkout_session_completed(session):
    """Process completed checkout session"""
    try:
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_id = metadata.get('plan_id')
        payment_intent_id = session.get('payment_intent')
        
        if not user_id or not plan_id:
            logger.error("Missing user_id or plan_id in session metadata")
            return
        
        from users.models import CustomUser
        
        user = CustomUser.objects.get(id=user_id)
        plan = SubscriptionPlan.objects.get(id=plan_id)
        
        subscription, created = UserSubscription.objects.update_or_create(
            user=user,
            defaults={
                'plan': plan,
                'status': 'active',
                'stripe_payment_intent_id': payment_intent_id
            }
        )
        
        Payment.objects.create(
            user=user,
            plan=plan,
            subscription=subscription,
            stripe_payment_intent_id=payment_intent_id,
            amount=plan.price,
            currency='USD',
            status='completed'
        )
        
        MessageUsage.objects.get_or_create(user=user)
        
        logger.info(f"Subscription {'created' if created else 'updated'} for user {user.email}")
        
    except Exception as e:
        logger.error(f"Error handling checkout session: {str(e)}")

def handle_payment_failed(payment_intent):
    """Handle failed payment"""
    try:
        payment_intent_id = payment_intent['id']
        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            payment.status = 'failed'
            payment.save()
            logger.info(f"Payment {payment_intent_id} marked as failed")
        except Payment.DoesNotExist:
            logger.warning(f"Payment not found for intent {payment_intent_id}")
            
    except Exception as e:
        logger.error(f"Error handling failed payment: {str(e)}")

def success_view(request):
    """Payment success page"""
    session_id = request.GET.get('session_id')
    return JsonResponse({
        'status': 'success',
        'message': 'Payment completed successfully!',
        'session_id': session_id
    })

def cancel_view(request):
    """Payment cancel page"""
    return JsonResponse({
        'status': 'cancelled',
        'message': 'Payment was cancelled.'
    })