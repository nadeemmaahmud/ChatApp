from django.core.management.base import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Create a test user for WebSocket testing'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='test@example.com', help='User email')
        parser.add_argument('--password', type=str, default='password123', help='User password')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        if CustomUser.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email {email} already exists')
            )
            return
        
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            is_verified=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test user:\n'
                f'Email: {email}\n'
                f'Password: {password}\n'
                f'User is verified and ready to use!'
            )
        )