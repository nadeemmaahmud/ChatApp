from django.db import models
from django.utils import timezone
from users.models import CustomUser as User
import uuid
from datetime import timedelta

class SubscriptionPlan(models.Model):
    PLAN_TYPES = (
        ('basic', 'Basic'),
        ('pro', 'Pro'),
    )
    
    DURATION_CHOICES = (
        (0, 'Unlimited'),
        (1, '1 Day'),
        (7, '7 Days'),
        (15, '15 Days'),
        (30, '30 Days'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(choices=DURATION_CHOICES)
    message_limit = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

    class Meta:
        ordering = ['price']

class UserSubscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"

    def is_active_subscription(self):
        """Check if subscription is still active"""
        if self.status != 'active':
            return False
        if self.end_date and timezone.now() > self.end_date:
            self.status = 'expired'
            self.save()
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.end_date and self.plan.duration_days > 0:
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - ${self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']

class MessageUsage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='message_usage')
    daily_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.daily_count} messages today"

    def reset_daily_count_if_needed(self):
        """Reset daily count if it's a new day"""
        today = timezone.now().date()
        if self.last_reset_date < today:
            self.daily_count = 0
            self.last_reset_date = today
            self.save()

    def can_send_message(self):
        """Check if user can send a message based on their subscription"""
        self.reset_daily_count_if_needed()
        
        try:
            subscription = self.user.subscription
            if subscription.is_active_subscription():
                if subscription.plan.message_limit is None:
                    return True
                return self.daily_count < subscription.plan.message_limit
        except UserSubscription.DoesNotExist:
            pass
        
        return self.daily_count < 10

    def increment_usage(self):
        """Increment message usage counters"""
        self.reset_daily_count_if_needed()
        self.daily_count += 1
        self.total_count += 1
        self.save()

    def get_remaining_messages(self):
        """Get remaining messages for today"""
        self.reset_daily_count_if_needed()
        
        try:
            subscription = self.user.subscription
            if subscription.is_active_subscription():
                if subscription.plan.message_limit is None:
                    return float('inf')
                return max(0, subscription.plan.message_limit - self.daily_count)
        except UserSubscription.DoesNotExist:
            pass
        
        return max(0, 10 - self.daily_count)