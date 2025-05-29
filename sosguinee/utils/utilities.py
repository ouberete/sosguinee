from page.models import UserDetails, EmailContent
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

class Utilities():

    @staticmethod
    def get_user_details(user):
        return UserDetails.objects.get(user=user)

    @staticmethod
    def get_user_categories(user):
        return UserDetails.objects.filter(user=user)
    
    @staticmethod
    def get_user_category(user, category):
        return UserDetails.objects.get(user=user, user_category=category)
        
    
    @staticmethod
    def sending_email(template, to, context, subject):
               
       message = render_to_string(template, context)
       plain_message = strip_tags(message)

       # Saving email content!
       content_email = EmailContent()
       content_email.subjet=subject
       content_email.plain_message =plain_message
       content_email.sender_email=settings.EMAIL_HOST_USER
       content_email.receiver_email=to
       content_email.html_message=message
       content_email.save()

       send_mail(
                    subject= subject,
                    message= plain_message,
                    html_message= message,
                    from_email= settings.EMAIL_HOST_USER,
                    recipient_list=to,
                    fail_silently=False,
                )
        
       content_email.is_sent = True
       content_email.date_sent = timezone.now()
       content_email.save()
