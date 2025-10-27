from django.contrib import admin
from .models import Plan, Subscription, Payment, MessageUsage

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'duration_days', 'price', 'message_limit', 'is_active']
    list_filter = ['plan_type', 'is_active', 'duration_days']
    search_fields = ['name']
    ordering = ['plan_type', 'price']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'is_active']
    list_filter = ['status', 'is_active', 'plan__plan_type']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    date_hierarchy = 'start_date'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'status', 'created_at']
    list_filter = ['status', 'currency', 'plan__plan_type']
    search_fields = ['user__email', 'stripe_payment_intent_id']
    raw_id_fields = ['user', 'subscription']
    date_hierarchy = 'created_at'
    readonly_fields = ['stripe_payment_intent_id']

@admin.register(MessageUsage)
class MessageUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'messages_sent_today', 'total_messages_sent', 'last_reset_date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    readonly_fields = ['total_messages_sent', 'last_reset_date']
