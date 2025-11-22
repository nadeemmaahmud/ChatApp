from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, Payment, MessageUsage


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'duration_days', 'message_limit', 'is_active', 'created_at']
    list_filter = ['plan_type', 'is_active', 'duration_days']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at']
    ordering = ['price']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'is_active_subscription']
    list_filter = ['status', 'plan']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'start_date']
    date_hierarchy = 'start_date'
    
    def is_active_subscription(self, obj):
        return obj.is_active_subscription()
    is_active_subscription.boolean = True
    is_active_subscription.short_description = 'Active'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['user__email', 'stripe_payment_intent_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(MessageUsage)
class MessageUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_count', 'total_count', 'last_reset_date', 'can_send', 'remaining']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'last_reset_date'
    
    def can_send(self, obj):
        return obj.can_send_message()
    can_send.boolean = True
    can_send.short_description = 'Can Send'
    
    def remaining(self, obj):
        remaining = obj.get_remaining_messages()
        return remaining if remaining != float('inf') else '∞'
    remaining.short_description = 'Remaining Today'