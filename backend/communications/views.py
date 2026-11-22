from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle

from .gemini import GeminiAnswerError, GeminiConfigurationError, generate_faq_answer
from .serializers import (
    ContactMessageSerializer,
    FAQQuestionSerializer,
    NewsletterSubscriberSerializer,
)


class PublicSubmissionView(CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]


class ContactMessageCreateView(PublicSubmissionView):
    serializer_class = ContactMessageSerializer
    throttle_scope = "contact-submission"


class NewsletterSubscriberCreateView(PublicSubmissionView):
    serializer_class = NewsletterSubscriberSerializer
    throttle_scope = "newsletter-subscription"


class FAQAnswerView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "faq-answer"

    def post(self, request):
        serializer = FAQQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            answer = generate_faq_answer(serializer.validated_data["question"])
        except GeminiConfigurationError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except GeminiAnswerError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"answer": answer}, status=status.HTTP_200_OK)
