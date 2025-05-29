
from datetime import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from page.models import EmailContent
from django.utils import timezone
class Utilities:
    #Sending email
    def sending_email(to, subject, template, context):
        msg = render_to_string(template, context)
        plain_message = strip_tags(msg)
        
        # Saving email content!
        content_email = EmailContent()
        content_email.subjet=subject
        content_email.plain_message =plain_message
        content_email.sender_email=settings.EMAIL_HOST_USER
        content_email.receiver_email=to
        content_email.html_message=msg
        content_email.save()
        # Content Email saved
        
        send_mail(subject, plain_message, settings.EMAIL_HOST_USER, to, html_message=msg)
        
        content_email.is_sent = True
        content_email.date_sent = timezone.now()
        content_email.save()
    