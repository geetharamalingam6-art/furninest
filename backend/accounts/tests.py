from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.test import override_settings
from django.test import TestCase
from rest_framework.test import APIClient
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from .models import Address


class UserManagerTests(TestCase):
    def test_create_user_normalizes_email_and_hashes_password(self):
        user = get_user_model().objects.create_user(
            "Shopper@Example.com",
            "test-password-123",
        )

        self.assertEqual(user.email, "shopper@example.com")
        self.assertTrue(user.check_password("test-password-123"))
        self.assertNotEqual(user.password, "test-password-123")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CustomerAuthApiTests(TestCase):
    password = "FurniNest-Secure-Account-742!"

    def setUp(self):
        self.client = APIClient()
        cache.clear()
        mail.outbox.clear()

    def register(self, email="Shopper@example.com"):
        return self.client.post(
            "/api/auth/register/",
            {
                "full_name": "Sample Shopper",
                "email": email,
                "phone_number": "9876543210",
                "password": self.password,
                "password_confirm": self.password,
            },
            format="json",
        )

    def verify_from_email(self, email_message):
        link = next(line.strip() for line in email_message.body.splitlines() if "/verify-email?" in line)
        query = parse_qs(urlsplit(link).query)
        return self.client.post(
            "/api/email/verify/",
            {"uid": query["uid"][0], "token": query["token"][0]},
            format="json",
        )

    def test_registration_sends_verification_and_verification_enables_login(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        self.assertIn("check your email", response.data["detail"].lower())
        user = get_user_model().objects.get(email="shopper@example.com")
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)
        login_before_verification = self.client.post(
            "/api/auth/login/",
            {"email": "shopper@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(login_before_verification.status_code, 400)
        self.assertIn("verify your email", str(login_before_verification.data).lower())

        verified = self.verify_from_email(mail.outbox[0])
        self.assertEqual(verified.status_code, 200)
        already_verified = self.verify_from_email(mail.outbox[0])
        self.assertEqual(already_verified.status_code, 200)
        self.assertIn("already verified", already_verified.data["detail"].lower())
        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        login_after_verification = self.client.post(
            "/api/auth/login/",
            {"email": "SHOPPER@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(login_after_verification.status_code, 200)
        self.assertTrue(login_after_verification.data["access"])
        self.assertEqual(len(mail.outbox), 2)  # verification and welcome

    def test_login_and_refresh_use_email_identity(self):
        self.register()
        self.verify_from_email(mail.outbox[0])

        response = self.client.post(
            "/api/auth/login/",
            {"email": "SHOPPER@example.com", "password": self.password},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["email"], "shopper@example.com")
        refreshed = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn("access", refreshed.data)

    def test_logout_blacklists_the_authenticated_users_refresh_token(self):
        self.register()
        self.verify_from_email(mail.outbox[0])
        response = self.client.post(
            "/api/auth/login/",
            {"email": "shopper@example.com", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

        logout = self.client.post(
            "/api/auth/logout/",
            {"refresh": response.data["refresh"]},
            format="json",
        )

        self.assertEqual(logout.status_code, 204)
        refresh = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh.status_code, 401)

    def test_duplicate_registration_and_unauthorized_profile_are_rejected(self):
        self.register()
        duplicate = self.register(email="shopper@example.com")
        profile = self.client.get("/api/profile/")

        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(profile.status_code, 401)

    def test_resend_verification_uses_enumeration_safe_response(self):
        self.register()
        mail.outbox.clear()
        known = self.client.post(
            "/api/email/resend-verification/",
            {"email": "shopper@example.com", "password": self.password},
            format="json",
        )
        unknown = self.client.post(
            "/api/email/resend-verification/",
            {"email": "missing@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(known.status_code, 200)
        self.assertIn("Verification email sent", known.data["detail"])
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_resend_verification_reports_smtp_delivery_failure(self):
        self.register()
        with patch("accounts.views.send_verification_email", side_effect=OSError("SMTP unavailable")):
            response = self.client.post(
                "/api/email/resend-verification/",
                {"email": "shopper@example.com", "password": self.password},
                format="json",
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("could not send", response.data["detail"].lower())

    def test_registration_reports_when_verification_email_cannot_be_sent(self):
        with patch("accounts.views.send_verification_email", side_effect=OSError("SMTP unavailable")):
            response = self.register()

        self.assertEqual(response.status_code, 201)
        self.assertIn("could not send", response.data["detail"].lower())
        user = get_user_model().objects.get(email="shopper@example.com")
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_change_keeps_old_address_until_new_address_is_verified(self):
        self.register()
        self.verify_from_email(mail.outbox[0])
        login = self.client.post(
            "/api/auth/login/",
            {"email": "shopper@example.com", "password": self.password},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        changed = self.client.post(
            "/api/account/change-email/",
            {"email": "new-shopper@example.com"},
            format="json",
        )
        self.assertEqual(changed.status_code, 200)
        user = get_user_model().objects.get(pk=login.data["user"]["id"])
        self.assertEqual(user.email, "shopper@example.com")
        self.assertEqual(user.pending_email, "new-shopper@example.com")

        verification = self.verify_from_email(mail.outbox[-1])
        self.assertEqual(verification.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.email, "new-shopper@example.com")
        self.assertTrue(user.email_verified)


class AddressApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "address@example.com",
            "secure-password",
        )
        self.other_user = get_user_model().objects.create_user(
            "other@example.com",
            "secure-password",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.address_payload = {
            "label": "Home",
            "full_name": "Address Shopper",
            "phone_number": "9876543210",
            "address_line_1": "12 Example Road",
            "city": "Pune",
            "state": "Maharashtra",
            "postal_code": "411001",
            "country": "India",
        }

    def test_first_address_becomes_default_and_is_private_to_its_owner(self):
        created = self.client.post("/api/addresses/", self.address_payload, format="json")

        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.data["is_default"])
        self.client.force_authenticate(self.other_user)
        response = self.client.get(f"/api/addresses/{created.data['id']}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Address.objects.filter(user=self.user).count(), 1)

    def test_address_can_be_edited_and_other_customers_cannot_change_or_delete_it(self):
        created = self.client.post("/api/addresses/", self.address_payload, format="json")
        edited = self.client.patch(
            f"/api/addresses/{created.data['id']}/",
            {"label": "Apartment", "city": "Mumbai"},
            format="json",
        )
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.data["label"], "Apartment")
        self.assertEqual(edited.data["city"], "Mumbai")

        self.client.force_authenticate(self.other_user)
        denied_update = self.client.patch(
            f"/api/addresses/{created.data['id']}/",
            {"city": "Private"},
            format="json",
        )
        denied_delete = self.client.delete(f"/api/addresses/{created.data['id']}/")
        self.assertEqual(denied_update.status_code, 404)
        self.assertEqual(denied_delete.status_code, 404)


class ProfileAndPasswordApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "profile@example.com",
            "Original-Password-948!",
            first_name="Profile",
            last_name="Customer",
            phone_number="9876543210",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_profile_update_and_password_change(self):
        profile = self.client.get("/api/profile/")
        self.assertEqual(profile.status_code, 200)
        updated = self.client.patch(
            "/api/profile/",
            {"full_name": "Updated Customer", "phone_number": "9999999999"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Customer")

        changed = self.client.post(
            "/api/auth/change-password/",
            {
                "old_password": "Original-Password-948!",
                "new_password": "New-Strong-Password-382!",
                "new_password_confirm": "New-Strong-Password-382!",
            },
            format="json",
        )
        self.assertEqual(changed.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-Strong-Password-382!"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_email_links_to_frontend_and_reset_token_is_one_time(self):
        requested = self.client.post(
            "/api/auth/forgot-password/",
            {"email": self.user.email},
            format="json",
        )
        self.assertEqual(requested.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        reset_url = next(
            line for line in mail.outbox[0].body.splitlines() if "reset-password?" in line
        )
        query = reset_url.split("?", 1)[1]
        from urllib.parse import parse_qs

        params = parse_qs(query)
        confirm = self.client.post(
            "/api/auth/reset-password/",
            {
                "uid": params["uid"][0],
                "token": params["token"][0],
                "new_password": "Reset-Strong-Password-382!",
                "new_password_confirm": "Reset-Strong-Password-382!",
            },
            format="json",
        )
        self.assertEqual(confirm.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Reset-Strong-Password-382!"))
