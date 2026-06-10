import ast

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


def parse_recipients(value):
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    if not text:
        return []

    try:
        parsed = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        parsed = None

    if isinstance(parsed, (list, tuple, set)):
        return [str(item).strip() for item in parsed if str(item).strip()]

    return [item.strip() for item in text.replace(';', ',').split(',') if item.strip()]


def resend_email_content(email_content):
    recipients = parse_recipients(email_content.receiver_email)
    if not recipients:
        raise ValueError("Aucun destinataire disponible pour cet email.")

    sent_count = send_mail(
        subject=email_content.subjet or "",
        message=email_content.plain_message or "",
        html_message=email_content.html_message or None,
        from_email=email_content.sender_email or settings.EMAIL_HOST_USER,
        recipient_list=recipients,
        fail_silently=False,
    )

    if sent_count:
        email_content.is_sent = True
        email_content.date_sent = timezone.now()
        email_content.save(update_fields=['is_sent', 'date_sent', 'updated_at'])

    return sent_count
