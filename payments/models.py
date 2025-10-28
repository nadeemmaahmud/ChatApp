from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()

class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
    ]
    
    DURATION_CHOICES = [
        (0, 'Unlimited'),
        (1, '1 Day'),
        (7, '7 Days'),
        (15, '15 Days'),
        (30, '30 Days'),
    ]
    
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

class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    
    def save(self, *args, **kwargs):
        if self.plan.duration_days > 0 and not self.end_date:
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        if self.end_date and timezone.now() > self.end_date:
            return True
        return False
    
    def days_remaining(self):
        if self.end_date:
            remaining = self.end_date - timezone.now()
            return max(0, remaining.days)
        return None

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"

class MessageUsage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='message_usage')
    daily_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)
    last_reset_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def reset_daily_count_if_needed(self):
        today = timezone.now().date()
        if self.last_reset_date < today:
            self.daily_count = 0
            self.last_reset_date = today
            self.save()

    def can_send_message(self):
        self.reset_daily_count_if_needed()
        
        try:
            subscription = self.user.subscription
            if subscription.plan.plan_type == 'pro' and subscription.status == 'active' and not subscription.is_expired():
                return True
            elif subscription.plan.plan_type == 'basic':
                return self.daily_count < (subscription.plan.message_limit or 50)
        except UserSubscription.DoesNotExist:
            pass
        
        return self.daily_count < 50

    def increment_usage(self):
        self.reset_daily_count_if_needed()
        self.daily_count += 1
        self.total_count += 1
        self.save()

    def __str__(self):
        return f"{self.user.email} - {self.daily_count} messages today"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - ${self.amount}"
    
    from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation {self.id}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                message_usage = self.sender.message_usage
                if not message_usage.can_send_message():
                    raise ValidationError("Message limit exceeded. Please upgrade to Pro plan.")
                message_usage.increment_usage()
            except:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Message from {self.sender.email} at {self.timestamp}"