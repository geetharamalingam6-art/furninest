from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_branded_email(
    *, subject, recipient, heading, greeting, message, button_label="", button_url="", details=None
):
    context = {
        "subject": subject,
        "heading": heading,
        "greeting": greeting,
        "message": message,
        "button_label": button_label,
        "button_url": button_url,
        "details": details or [],
        "support_email": settings.SUPPORT_EMAIL,
        "store_url": settings.FRONTEND_BASE_URL,
    }
    text = render_to_string("emails/notification.txt", context)
    html = render_to_string("emails/notification.html", context)
    email = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )
    email.attach_alternative(html, "text/html")
    return email.send(fail_silently=False)
