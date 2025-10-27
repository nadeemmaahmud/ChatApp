from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Plan(models.Model):
    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
    ]
    
    DURATION_CHOICES = [
        (1, '1 Day'),
        (7, '7 Days'),
        (15, '15 Days'),
        (30, '30 Days'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    duration_days = models.IntegerField(choices=DURATION_CHOICES, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    message_limit = models.IntegerField(help_text="Number of messages allowed. -1 for unlimited")
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        if self.plan_type == 'basic':
            return f"{self.name} - {self.message_limit} messages"
        return f"{self.name} - {self.get_duration_days_display()}"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.plan and self.plan.duration_days and not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        if self.end_date:
            return timezone.now() > self.end_date
        return False
    
    @property
    def days_remaining(self):
        if self.end_date:
            remaining = self.end_date - timezone.now()
            return max(0, remaining.days)
        return 0
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    stripe_payment_intent_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} - ${self.amount}"


class MessageUsage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='message_usage')
    messages_sent_today = models.IntegerField(default=0)
    total_messages_sent = models.IntegerField(default=0)
    last_reset_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def reset_daily_count(self):
        today = timezone.now().date()
        if self.last_reset_date < today:
            self.messages_sent_today = 0
            self.last_reset_date = today
            self.save()
    
    def can_send_message(self):
        self.reset_daily_count()
        
        try:
            subscription = self.user.subscription
            if subscription.is_active and not subscription.is_expired:
                if subscription.plan.message_limit == -1:
                    return True
                return self.messages_sent_today < subscription.plan.message_limit
        except Subscription.DoesNotExist:
            pass
        
        return self.messages_sent_today < 50
    
    def increment_message_count(self):
        self.reset_daily_count()
        self.messages_sent_today += 1
        self.total_messages_sent += 1
        self.save()
    
    def __str__(self):
        return f"{self.user.email} - {self.messages_sent_today} messages today"
