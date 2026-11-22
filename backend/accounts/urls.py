from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AddressViewSet,
    ChangePasswordView,
    ChangeEmailView,
    ResendVerificationEmailView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    VerifyEmailView,
)

router = DefaultRouter()
router.register("addresses", AddressViewSet, basename="address")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("email/verify/", VerifyEmailView.as_view(), name="email-verify"),
    path("email/resend-verification/", ResendVerificationEmailView.as_view(), name="email-resend-verification"),
    path("account/change-email/", ChangeEmailView.as_view(), name="account-change-email"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/forgot-password/", PasswordResetRequestView.as_view(), name="forgot-password"),
    path("auth/reset-password/", PasswordResetConfirmView.as_view(), name="reset-password"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("", include(router.urls)),
]
