from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode

from page.models import EmailContent
from sosguinee.utils.email_retry import resend_email_content


ACTIVATION_EMAIL_SUBJECT = "Activation de votre compte SOS Guinee"


def site_protocol_domain():
    site_url = (getattr(settings, "SITE_URL", "") or "http://localhost:8000").rstrip("/")
    parsed = urlparse(site_url)
    protocol = parsed.scheme or ("https" if not settings.DEBUG else "http")
    domain = parsed.netloc or parsed.path
    return protocol, domain


def activation_email_context(user):
    protocol, domain = site_protocol_domain()
    return {
        "user": user,
        "domain": domain,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "protocol": protocol,
        "token": default_token_generator.make_token(user),
    }


def _existing_unsent_activation_email(user):
    if not user.email:
        return None

    return (
        EmailContent.objects
        .filter(
            is_sent=False,
            receiver_email__icontains=user.email,
            subjet=ACTIVATION_EMAIL_SUBJECT,
        )
        .order_by("-created_at")
        .first()
    )


def send_or_queue_activation_email(user, reuse_unsent=True):
    if reuse_unsent:
        existing_email = _existing_unsent_activation_email(user)
        if existing_email:
            resend_email_content(existing_email)
            return existing_email

    html_message = render_to_string(
        "accounts/account_activation_email.html",
        activation_email_context(user),
    )
    email_content = EmailContent.objects.create(
        subjet=ACTIVATION_EMAIL_SUBJECT,
        plain_message=strip_tags(html_message),
        sender_email=getattr(settings, "EMAIL_HOST_USER", ""),
        receiver_email=user.email,
        html_message=html_message,
        is_sent=False,
    )
    resend_email_content(email_content)
    return email_content
