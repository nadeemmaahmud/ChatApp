from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan, UserSubscription, MessageUsage

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_subscription(sender, instance, created, **kwargs):
    if created:
        basic_plan, _ = SubscriptionPlan.objects.get_or_create(
            plan_type='basic',
            defaults={
                'name': 'Basic Plan',
                'price': 0.00,
                'duration_days': 0,
                'message_limit': 50,
            }
        )
        
        UserSubscription.objects.create(
            user=instance,
            plan=basic_plan
        )
        
        MessageUsage.objects.create(user=instance)