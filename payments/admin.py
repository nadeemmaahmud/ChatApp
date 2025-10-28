from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, MessageUsage, Payment

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'duration_days', 'message_limit', 'is_active']
    list_filter = ['plan_type', 'is_active']

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date']
    list_filter = ['status', 'plan']

@admin.register(MessageUsage)
class MessageUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_count', 'total_count', 'last_reset_date']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'plan', 'created_at']
    list_filter = ['status', 'plan']