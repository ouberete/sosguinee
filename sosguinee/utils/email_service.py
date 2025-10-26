from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

class EmailService:
    @staticmethod
    def send_subscription_notification(user, context):
        """Envoie un email de confirmation d'abonnement"""
        subject = 'Confirmation de votre abonnement'
        html_message = render_to_string('emails/subscription_confirmation.html', {
            'user': user,
            'site_url': settings.SITE_URL,
            **context
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False
        )

    @staticmethod
    def send_alert_notification(alert):
        """Envoie un email de notification pour une nouvelle alerte"""
        subject = f'Nouvelle alerte de perte - {alert.name}'
        html_message = render_to_string('emails/alert_notification.html', {
            'alert': alert,
            'site_url': settings.SITE_URL
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[alert.user.email],
            fail_silently=False
        )

    @staticmethod
    def send_funding_request_notification(funding_request):
        """Envoie un email de notification pour une nouvelle demande de financement"""
        subject = f'Nouvelle demande de financement - {funding_request.title}'
        html_message = render_to_string('emails/funding_request_notification.html', {
            'funding_request': funding_request,
            'site_url': settings.SITE_URL
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[funding_request.user.email],
            fail_silently=False
        )

    @staticmethod
    def send_donation_notification(donation):
        """Envoie un email de notification pour un nouveau don"""
        subject = 'Merci pour votre don!'
        html_message = render_to_string('emails/donation_notification.html', {
            'donation': donation,
            'site_url': settings.SITE_URL
        })
        plain_message = strip_tags(html_message)
        
        # Email au donateur
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[donation.donor.email],
            fail_silently=False
        )
        
        # Email au bénéficiaire
        if donation.funding_request and donation.funding_request.user:
            subject = 'Vous avez reçu un nouveau don!'
            html_message = render_to_string('emails/donation_received_notification.html', {
                'donation': donation,
                'site_url': settings.SITE_URL
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[donation.funding_request.user.email],
                fail_silently=False
            )

    @staticmethod
    def send_subscription_reminder(user):
        """Envoie un rappel d'abonnement"""
        subject = 'Rappel d\'abonnement'
        html_message = render_to_string('emails/subscription_reminder.html', {
            'user': user,
            'site_url': settings.SITE_URL
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False
        )