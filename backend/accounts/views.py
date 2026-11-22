import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from communications.mailer import send_branded_email
from .models import Address, UserProfile
from .emailing import send_verification_email, send_welcome_email, verification_token_is_valid
from .serializers import (
    AddressSerializer,
    ChangePasswordSerializer,
    EmailTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSummarySerializer,
    VerificationResendSerializer,
)

logger = logging.getLogger(__name__)


def log_email_delivery_failure(user_id, operation, error):
    logger.error(
        "Account email delivery failed (user_id=%s, operation=%s, error_type=%s, smtp_code=%s).",
        user_id,
        operation,
        type(error).__name__,
        getattr(error, "smtp_code", None),
    )


def try_send_account_email(user_id, operation, callback):
    try:
        callback()
    except Exception:
        logger.exception("Account email delivery failed (user_id=%s, operation=%s).", user_id, operation)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        try:
            send_verification_email(user)
        except Exception as error:
            log_email_delivery_failure(user.pk, "verification", error)
            return Response(
                {
                    "detail": (
                        "Your account was created, but we could not send the verification email. "
                        "Check the backend email settings, then use Resend Verification Email."
                    )
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {
                "detail": "Your account has been created! Please check your email to verify your account."
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-login"


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email-verify"

    def post(self, request):
        uid = request.data.get("uid", "")
        token = request.data.get("token", "")
        try:
            user_id = urlsafe_base64_decode(uid).decode("utf-8")
            user = get_user_model().objects.get(pk=user_id)
        except (TypeError, ValueError, UnicodeDecodeError, get_user_model().DoesNotExist):
            raise ValidationError({"detail": "This verification link is invalid or expired."})
        if user.email_verified and not user.pending_email:
            return Response({"detail": "This email address is already verified. You can sign in."})
        if not verification_token_is_valid(user, token):
            raise ValidationError({"detail": "This verification link is invalid or expired."})

        changed_email = bool(user.pending_email)
        if changed_email:
            if get_user_model().objects.filter(email__iexact=user.pending_email).exclude(pk=user.pk).exists():
                raise ValidationError({"detail": "This email address is no longer available."})
            user.email = user.pending_email
            user.pending_email = ""
        first_verification = not user.email_verified
        user.email_verified = True
        user.email_verification_token_hash = ""
        user.email_verification_sent_at = None
        user.save(update_fields=[
            "email", "pending_email", "email_verified",
            "email_verification_token_hash", "email_verification_sent_at",
        ])
        if first_verification:
            try_send_account_email(user.pk, "welcome", lambda: send_welcome_email(user))
        return Response({"detail": "Your email address has been verified. You can now sign in."})


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email-resend"

    def post(self, request):
        serializer = VerificationResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().casefold()
        if request.user.is_authenticated:
            user = request.user
            if email not in {user.email.casefold(), user.pending_email.casefold()}:
                return Response(
                    {"detail": "If your account needs verification, a link will be sent to its email address."}
                )
            recipient = user.pending_email or user.email
        else:
            user = get_user_model().objects.filter(email__iexact=email).first()
            password = serializer.validated_data.get("password", "")
            if not user or not user.check_password(password):
                return Response(
                    {"detail": "If the email and password match an unverified account, a link will be sent."}
                )
            recipient = user.email

        if user.email_verified and not user.pending_email:
            return Response({"detail": "This email address is already verified. You can sign in."})
        try:
            send_verification_email(user, recipient=recipient)
        except Exception as error:
            log_email_delivery_failure(user.pk, "verification-resend", error)
            return Response(
                {
                    "detail": (
                        "We could not send the verification email. Check EMAIL_HOST_USER, "
                        "EMAIL_HOST_PASSWORD, and your Gmail App Password, then try again."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"detail": "Verification email sent. Check your inbox and spam folder."})


class ChangeEmailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "email-change"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().casefold()
        if email == request.user.email:
            raise ValidationError({"email": "Enter a different email address."})
        if get_user_model().objects.filter(
            Q(email__iexact=email) | Q(pending_email__iexact=email)
        ).exclude(pk=request.user.pk).exists():
            raise ValidationError({"email": "An account with this email already exists."})
        request.user.pending_email = email
        request.user.save(update_fields=["pending_email"])
        send_verification_email(request.user, recipient=email)
        return Response({"detail": "Check your new email address for a verification link."})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_refresh = request.data.get("refresh")
        if not raw_refresh:
            raise ValidationError({"refresh": "A refresh token is required."})
        try:
            refresh = RefreshToken(raw_refresh)
        except TokenError as error:
            raise ValidationError({"refresh": "The refresh token is invalid or expired."}) from error
        if str(refresh.get("user_id")) != str(request.user.pk):
            raise PermissionDenied("This refresh token does not belong to the authenticated user.")
        refresh.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password-reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().casefold()
        user = get_user_model().objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = (
                f"{settings.FRONTEND_BASE_URL}/reset-password?uid={uid}&token={token}"
            )
            try_send_account_email(
                user.pk,
                "password-reset",
                lambda: send_branded_email(
                    subject="Reset Your FurniNest Password",
                    recipient=user.email,
                    heading="Reset your password",
                    greeting=f"Hello {user.get_full_name().strip() or 'there'},",
                    message="We received a request to reset your FurniNest account password. Use the link below within one hour to choose a new password. If you did not request this change, you can safely ignore this email.",
                    button_label="Reset My Password",
                    button_url=reset_url,
                ),
            )
        return Response(
            {"detail": "If an account exists for that email, password reset instructions have been sent."}
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password-reset-confirm"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Your password has been updated successfully. You can now sign in."})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get_profile(self, user):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile

    def get(self, request):
        return Response(ProfileSerializer(self.get_profile(request.user), context={"request": request}).data)

    def patch(self, request):
        profile = self.get_profile(request.user)
        serializer = ProfileSerializer(
            profile,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password-change"

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "Your password has been changed."})


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        user_addresses = Address.objects.filter(user=self.request.user)
        is_first = not user_addresses.exists()
        is_default = serializer.validated_data.get("is_default", False) or is_first
        if is_default:
            user_addresses.update(is_default=False)
        serializer.save(user=self.request.user, is_default=is_default)

    @transaction.atomic
    def perform_update(self, serializer):
        make_default = serializer.validated_data.get(
            "is_default",
            serializer.instance.is_default,
        )
        if make_default:
            Address.objects.filter(user=self.request.user).exclude(pk=serializer.instance.pk).update(
                is_default=False
            )
        serializer.save(is_default=make_default)
import logging

