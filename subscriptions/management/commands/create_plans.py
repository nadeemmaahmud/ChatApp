from django.core.management.base import BaseCommand
from subscriptions.models import Plan

class Command(BaseCommand):
    help = 'Create default subscription plans'

    def handle(self, *args, **options):
        basic_plan, created = Plan.objects.get_or_create(
            name='Basic Plan',
            plan_type='basic',
            defaults={
                'duration_days': None,
                'price': 0.00,
                'message_limit': 50,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {basic_plan.name}'))
        else:
            self.stdout.write(f'Already exists: {basic_plan.name}')

        pro_plans = [
            {
                'name': 'Pro 1 Day',
                'duration_days': 1,
                'price': 2.99,
            },
            {
                'name': 'Pro 7 Days',
                'duration_days': 7,
                'price': 9.99,
            },
            {
                'name': 'Pro 15 Days',
                'duration_days': 15,
                'price': 19.99,
            },
            {
                'name': 'Pro 30 Days',
                'duration_days': 30,
                'price': 29.99,
            }
        ]

        for plan_data in pro_plans:
            plan, created = Plan.objects.get_or_create(
                name=plan_data['name'],
                plan_type='pro',
                defaults={
                    'duration_days': plan_data['duration_days'],
                    'price': plan_data['price'],
                    'message_limit': -1,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {plan.name}'))
            else:
                self.stdout.write(f'Already exists: {plan.name}')

        self.stdout.write(self.style.SUCCESS('Successfully created/updated all plans'))