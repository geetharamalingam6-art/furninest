from django.urls import path

from .views import ContactMessageCreateView, FAQAnswerView, NewsletterSubscriberCreateView

urlpatterns = [
    path("contact/", ContactMessageCreateView.as_view(), name="contact-submit"),
    path("newsletter/", NewsletterSubscriberCreateView.as_view(), name="newsletter-subscribe"),
    path("faq/answer/", FAQAnswerView.as_view(), name="faq-answer"),
]
