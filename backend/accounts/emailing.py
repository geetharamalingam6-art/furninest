import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from communications.mailer import send_branded_email


VERIFICATION_LIFETIME = timedelta(hours=24)


def verify_link(uid, token):
    query = urlencode({"uid": uid, "token": token})
    return f"{settings.FRONTEND_BASE_URL}/verify-email?{query}"


def send_verification_email(user, recipient=None):
    token = secrets.token_urlsafe(32)
    user.email_verification_token_hash = hashlib.sha256(token.encode()).hexdigest()
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=["email_verification_token_hash", "email_verification_sent_at"])
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    target = recipient or user.pending_email or user.email
    verification_link = verify_link(uid, token)
    return send_mail(
        subject="Verify Your FurniNest Account",
        message=(
            f"Welcome to FurniNest, {user.get_full_name().strip() or 'there'}!\n\n"
            "Please click the link below to verify your account. "
            "This link expires in 24 hours.\n\n"
            f"{verification_link}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[target],
        fail_silently=False,
    )


def verification_token_is_valid(user, token):
    if not token or not user.email_verification_token_hash or not user.email_verification_sent_at:
        return False
    if timezone.now() - user.email_verification_sent_at > VERIFICATION_LIFETIME:
        return False
    digest = hashlib.sha256(token.encode()).hexdigest()
    return secrets.compare_digest(digest, user.email_verification_token_hash)


def send_welcome_email(user):
    return send_branded_email(
        subject="Welcome to FurniNest!",
        recipient=user.email,
        heading="Make yourself at home.",
        greeting=f"Hello {user.get_full_name().strip() or 'there'},",
        message="Your email is verified and your FurniNest account is ready. Explore thoughtfully chosen furniture and pieces made for everyday living.",
        button_label="Explore Collections",
        button_url=f"{settings.FRONTEND_BASE_URL}/shop",
    )
