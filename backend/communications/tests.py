import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import ContactMessage, NewsletterSubscriber


class CommunicationSubmissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_contact_submission_is_saved(self):
        response = self.client.post(
            "/api/contact/",
            {
                "name": "  Alex Customer  ",
                "email": "alex@example.com",
                "phone": "+91 98765 43210",
                "subject": "Furniture question",
                "message": "Please tell me more about this item.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertEqual(ContactMessage.objects.get().name, "Alex Customer")

    def test_contact_submission_rejects_invalid_email_and_phone(self):
        response = self.client.post(
            "/api/contact/",
            {
                "name": "Alex Customer",
                "email": "not-an-email",
                "phone": "phone",
                "subject": "Question",
                "message": "Please help.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_newsletter_subscription_is_case_insensitive_and_idempotent(self):
        first = self.client.post(
            "/api/newsletter/",
            {"email": "  Alex@Example.com "},
            format="json",
        )
        second = self.client.post(
            "/api/newsletter/",
            {"email": "alex@example.com"},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)
        self.assertEqual(NewsletterSubscriber.objects.get().email, "alex@example.com")

    @override_settings(GEMINI_API_KEY="test-gemini-key", GEMINI_MODEL="gemini-test")
    def test_faq_question_returns_answer_from_gemini_without_exposing_key_in_url(self):
        gemini_response = BytesIO(
            json.dumps(
                {
                    "candidates": [
                        {"content": {"parts": [{"text": "Measure the room and doorways first."}]}}
                    ]
                }
            ).encode("utf-8")
        )

        with patch("communications.gemini.urlopen", return_value=gemini_response) as request:
            response = self.client.post(
                "/api/faq/answer/",
                {"question": "How do I choose the right furniture size?"},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"answer": "Measure the room and doorways first."})
        gemini_request = request.call_args.args[0]
        self.assertNotIn("test-gemini-key", gemini_request.full_url)
        self.assertEqual(gemini_request.get_header("X-goog-api-key"), "test-gemini-key")
        self.assertEqual(
            json.loads(gemini_request.data)["contents"][0]["parts"][0]["text"],
            "How do I choose the right furniture size?",
        )

    @override_settings(GEMINI_API_KEY="")
    def test_faq_question_requires_a_server_side_gemini_key(self):
        with patch("communications.gemini.urlopen") as request:
            response = self.client.post(
                "/api/faq/answer/",
                {"question": "Where can I find delivery information?"},
                format="json",
            )

        self.assertEqual(response.status_code, 503)
        request.assert_not_called()

    def test_faq_question_rejects_empty_text(self):
        with patch("communications.gemini.urlopen") as request:
            response = self.client.post(
                "/api/faq/answer/",
                {"question": "   "},
                format="json",
            )

        self.assertEqual(response.status_code, 400)
        request.assert_not_called()

    @override_settings(GEMINI_API_KEY="test-gemini-key")
    def test_faq_question_shows_actionable_message_when_gemini_rejects_key(self):
        error = HTTPError(
            "https://generativelanguage.googleapis.com/",
            403,
            "Forbidden",
            {},
            None,
        )
        with patch("communications.gemini.urlopen", side_effect=error):
            response = self.client.post(
                "/api/faq/answer/",
                {"question": "How do I care for a wooden table?"},
                format="json",
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("Gemini rejected the API key", response.data["detail"])
