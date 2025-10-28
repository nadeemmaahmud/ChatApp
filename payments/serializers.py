from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, MessageUsage, Payment

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'plan_type', 'price', 'duration_days', 'message_limit']

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'status', 'start_date', 'end_date', 'days_remaining', 'is_expired']
    
    def get_days_remaining(self, obj):
        return obj.days_remaining()
    
    def get_is_expired(self, obj):
        return obj.is_expired()

class MessageUsageSerializer(serializers.ModelSerializer):
    can_send_message = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageUsage
        fields = ['daily_count', 'total_count', 'last_reset_date', 'can_send_message']
    
    def get_can_send_message(self, obj):
        return obj.can_send_message()

class CreatePaymentIntentSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, plan_type='pro', is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Pro plan not found")