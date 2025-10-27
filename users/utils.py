from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from .models import EmailVerificationToken, PasswordResetToken, CustomUser
import logging

logger = logging.getLogger(__name__)

def send_verification_email(user: CustomUser) -> bool:
    EmailVerificationToken.objects.filter(user=user).delete()
    token = EmailVerificationToken.objects.create(user=user)

    base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8001").rstrip('/')
    verify_path = reverse("customuser-verify")
    verify_url = f"{base_url}{verify_path}?token={token.token}"

    subject = "Verify your ChatApp account"
    message = (
        "Hi,\n\nPlease verify your account by clicking the link below:\n"
        f"{verify_url}\n\nThis link expires in 24 hours."
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@chatapp.local")

    logger.info(f"[Email] To={user.email} URL={verify_url}")
    try:
        send_mail(subject, message, from_email, [user.email], fail_silently=False)
        logger.info("[Email] Sent successfully")
        return True
    except Exception as e:
        logger.exception(f"[Email] Failed: {e}")
        return False

def send_password_reset_email(user: CustomUser) -> bool:
    PasswordResetToken.objects.filter(user=user).delete()
    token = PasswordResetToken.objects.create(user=user)

    base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8001").rstrip('/')
    reset_path = reverse("customuser-reset-password")
    reset_url = f"{base_url}{reset_path}?token={token.token}"

    subject = "Reset your ChatApp password"
    message = (
        f"Hi {user.first_name or user.email},\n\n"
        "You requested a password reset for your ChatApp account.\n"
        "Click the link below to reset your password:\n\n"
        f"{reset_url}\n\n"
        "This link expires in 1 hour for security reasons.\n"
        "If you didn't request this reset, please ignore this email."
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@chatapp.local")

    logger.info(f"[Password Reset Email] To={user.email} URL={reset_url}")
    try:
        send_mail(subject, message, from_email, [user.email], fail_silently=False)
        logger.info("[Password Reset Email] Sent successfully")
        return True
    except Exception as e:
        logger.exception(f"[Password Reset Email] Failed: {e}")
        return False