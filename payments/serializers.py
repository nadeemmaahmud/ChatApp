from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, Payment, MessageUsage


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    plan_type_display = serializers.CharField(source='get_plan_type_display', read_only=True)
    duration_display = serializers.CharField(source='get_duration_days_display', read_only=True)
    
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'plan_type', 'plan_type_display', 'price', 
                 'duration_days', 'duration_display', 'message_limit', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'user_email', 'plan', 'status', 'start_date', 
                 'end_date', 'is_active', 'stripe_payment_intent_id']
        read_only_fields = ['id', 'start_date']
    
    def get_is_active(self, obj):
        return obj.is_active_subscription()


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'user_email', 'plan_name', 'amount', 'currency', 
                 'status', 'stripe_payment_intent_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MessageUsageSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    remaining_messages = serializers.SerializerMethodField()
    can_send = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageUsage
        fields = ['id', 'user_email', 'daily_count', 'total_count', 
                 'last_reset_date', 'remaining_messages', 'can_send', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_remaining_messages(self, obj):
        remaining = obj.get_remaining_messages()
        return remaining if remaining != float('inf') else 'unlimited'
    
    def get_can_send(self, obj):
        return obj.can_send_message()


class CreateCheckoutSessionSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField(required=True)
    
    def validate_plan_id(self, value):
        if not SubscriptionPlan.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive subscription plan")
        return value