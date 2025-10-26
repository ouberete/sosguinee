from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from celery import shared_task
from accounts.models import UserProfile
from sosguinee.utils.email_service import EmailService

@shared_task
def send_subscription_reminders():
    # Trouver les utilisateurs dont l'abonnement expire dans 7 jours
    expiry_threshold = timezone.now() + timedelta(days=7)
    users_to_remind = UserProfile.objects.filter(
        subscription_end_date__lte=expiry_threshold,
        subscription_end_date__gt=timezone.now(),
        subscription_reminder_sent=False
    )
    
    for profile in users_to_remind:
        try:
            EmailService.send_subscription_reminder(profile.user)
            profile.subscription_reminder_sent = True
            profile.save()
        except Exception as e:
            print(f"Erreur lors de l'envoi du rappel d'abonnement à {profile.user.email}: {str(e)}")

@shared_task
def cleanup_expired_subscriptions():
    # Désactiver les fonctionnalités premium pour les abonnements expirés
    expired_profiles = UserProfile.objects.filter(
        subscription_end_date__lt=timezone.now(),
        is_premium=True
    )
    
    for profile in expired_profiles:
        profile.is_premium = False
        profile.save()
        # Optionnel : envoyer un email pour informer l'utilisateur