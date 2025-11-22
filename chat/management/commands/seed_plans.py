from django.core.management.base import BaseCommand
from payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Seed subscription plans into the database'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Basic Plan',
                'plan_type': 'basic',
                'price': 0.00,
                'duration_days': 0,
                'message_limit': 10,
                'is_active': True,
            },
            {
                'name': 'Pro - Daily',
                'plan_type': 'pro',
                'price': 1.00,
                'duration_days': 1,
                'message_limit': None,  # Unlimited
                'is_active': True,
            },
            {
                'name': 'Pro - Weekly',
                'plan_type': 'pro',
                'price': 7.00,
                'duration_days': 7,
                'message_limit': None,  # Unlimited
                'is_active': True,
            },
            {
                'name': 'Pro - Monthly',
                'plan_type': 'pro',
                'price': 30.00,
                'duration_days': 30,
                'message_limit': None,  # Unlimited
                'is_active': True,
            },
            {
                'name': 'Pro - Yearly',
                'plan_type': 'pro',
                'price': 365.00,
                'duration_days': 365,
                'message_limit': None,  # Unlimited
                'is_active': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created plan: {plan.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated plan: {plan.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeeding complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
