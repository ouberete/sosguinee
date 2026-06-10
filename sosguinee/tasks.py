from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction

from page.models import Donation, FundPayment, FundingRequest, LossAlert
from sosguinee.utils.email_service import EmailService


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_email_task(self, recipient_list, subject, template_path, context=None, from_email=None):
    return EmailService.send_template_email(
        recipient_list=recipient_list,
        subject=subject,
        template_path=template_path,
        context=context or {},
        from_email=from_email,
        queue=False,
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_funding_request_notification_task(self, funding_request_id):
    funding_request = FundingRequest.objects.filter(id=funding_request_id).first()
    if not funding_request:
        return 0
    return EmailService.send_funding_request_notification(funding_request, queue=False)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_alert_notification_task(self, loss_alert_id):
    alert = LossAlert.objects.filter(id=loss_alert_id).first()
    if not alert:
        return 0
    return EmailService.send_alert_notification(alert, queue=False)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_donation_notification_task(self, donation_id):
    donation = Donation.objects.filter(id=donation_id).first()
    if not donation:
        return 0
    return EmailService.send_donation_notification(donation, queue=False)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_subscription_notification_task(self, user_id, context=None):
    user = get_user_model().objects.filter(id=user_id).first()
    if not user:
        return 0
    return EmailService.send_subscription_notification(user, context or {}, queue=False)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def send_subscription_reminder_task(self, user_id):
    user = get_user_model().objects.filter(id=user_id).first()
    if not user:
        return 0
    with transaction.atomic():
        return EmailService.send_subscription_reminder(user, queue=False)
