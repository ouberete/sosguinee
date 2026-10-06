import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def send_subscription_reminders(self):
    """Envoie un rappel aux utilisateurs dont l'abonnement expire dans 7 jours."""
    from accounts.models import UserSubscription
    from ensemble224.utils.email_service import EmailService

    now = timezone.now()
    expiry_threshold = now + timedelta(days=7)
    subscriptions_to_remind = UserSubscription.objects.filter(
        is_active=True,
        end_date__lte=expiry_threshold,
        end_date__gt=now,
        reminder_sent=False,
    ).select_related("user")

    reminded_ids = []
    for subscription in subscriptions_to_remind:
        try:
            sent = EmailService.send_subscription_reminder(subscription.user, queue=False)
            if sent:
                reminded_ids.append(subscription.pk)
        except Exception:
            logger.exception(
                "Erreur lors de l'envoi du rappel pour l'abonnement %s",
                subscription.pk,
            )

    if reminded_ids:
        UserSubscription.objects.filter(pk__in=reminded_ids).update(reminder_sent=True)

    logger.info("Rappels d'abonnement envoyés : %d", len(reminded_ids))
    return {"reminded": len(reminded_ids)}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def cleanup_expired_subscriptions(self):
    """Désactive le statut premium des abonnements expirés (bulk update)."""
    from accounts.models import UserSubscription

    updated = UserSubscription.objects.filter(
        end_date__lt=timezone.now(),
        is_active=True,
    ).update(is_active=False)

    logger.info("Abonnements expirés nettoyés : %d", updated)
    return {"cleaned": updated}
