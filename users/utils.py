from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from .models import EmailVerificationToken, CustomUser
import logging

logger = logging.getLogger(__name__)

def send_verification_email(user: CustomUser) -> bool:
    # remove old tokens
    EmailVerificationToken.objects.filter(user=user).delete()
    token = EmailVerificationToken.objects.create(user=user)

    base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip('/')
    verify_path = reverse("users-verify")
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