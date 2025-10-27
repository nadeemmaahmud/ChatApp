from rest_framework import serializers
from .models import Plan, Subscription, Payment, MessageUsage
from django.contrib.auth import get_user_model

User = get_user_model()

class PlanSerializer(serializers.ModelSerializer):
    duration_display = serializers.CharField(source='get_duration_days_display', read_only=True)
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'plan_type', 'duration_days', 'duration_display',
            'price', 'message_limit', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = PlanSerializer(source='plan', read_only=True)
    days_remaining = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_details', 'status', 'start_date', 'end_date',
            'is_active', 'days_remaining', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'days_remaining', 'is_expired']


class PaymentSerializer(serializers.ModelSerializer):
    plan_details = PlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'plan', 'plan_details', 'amount', 'currency', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MessageUsageSerializer(serializers.ModelSerializer):
    can_send_message = serializers.SerializerMethodField()
    remaining_messages = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageUsage
        fields = [
            'messages_sent_today', 'total_messages_sent', 'last_reset_date',
            'can_send_message', 'remaining_messages'
        ]
        read_only_fields = ['messages_sent_today', 'total_messages_sent', 'last_reset_date']
    
    def get_can_send_message(self, obj):
        return obj.can_send_message()
    
    def get_remaining_messages(self, obj):
        obj.reset_daily_count()
        try:
            subscription = obj.user.subscription
            if subscription.is_active and not subscription.is_expired:
                if subscription.plan.message_limit == -1:
                    return "unlimited"
                return max(0, subscription.plan.message_limit - obj.messages_sent_today)
        except Subscription.DoesNotExist:
            pass
        
        return max(0, 50 - obj.messages_sent_today)


class CreatePaymentIntentSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    
    def validate_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
            if plan.plan_type == 'basic':
                raise serializers.ValidationError("Cannot purchase basic plan")
            return value
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan")


class UserSubscriptionStatusSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    message_usage = MessageUsageSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'subscription', 'message_usage']
        read_only_fields = ['id', 'email']