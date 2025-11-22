from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Creates default subscription plans for the application'

    def handle(self, *args, **options):
        plans_data = [
            {
                'name': 'Basic Plan',
                'plan_type': 'basic',
                'price': 9.99,
                'duration_days': 30,
                'message_limit': 100,
                'is_active': True
            },
            {
                'name': 'Pro Plan',
                'plan_type': 'pro',
                'price': 19.99,
                'duration_days': 30,
                'message_limit': None,  # Unlimited
                'is_active': True
            },
        ]

        created_count = 0
        updated_count = 0

        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created plan: {plan.name} (${plan.price})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated plan: {plan.name} (${plan.price})')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new plans, updated {updated_count} existing plans.'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Note: Free tier (10 messages/day) is automatically available to all users without a subscription.'
            )
        )
