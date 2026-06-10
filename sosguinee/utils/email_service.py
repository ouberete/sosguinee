import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags


logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def _async_enabled():
        return bool(getattr(settings, "ASYNC_EMAIL_ENABLED", False))

    @staticmethod
    def _queue_task(task_name, *args, **kwargs):
        try:
            from sosguinee import tasks as async_tasks

            task = getattr(async_tasks, task_name)
            return task.delay(*args, **kwargs)
        except Exception as exc:
            logger.warning("Queue email indisponible, fallback sync (%s): %s", task_name, exc)
            return None

    @staticmethod
    def _send_mail_recorded(subject, plain_message, html_message, recipient_list, from_email=None):
        recipients = [email for email in (recipient_list or []) if email]
        if not recipients:
            return 0

        from page.models import EmailContent

        sender = from_email or settings.EMAIL_HOST_USER
        email_content = EmailContent.objects.create(
            subjet=subject,
            plain_message=plain_message,
            sender_email=sender,
            receiver_email=",".join(recipients),
            html_message=html_message,
            is_sent=False,
        )

        sent_count = send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=sender,
            recipient_list=recipients,
            fail_silently=False,
        )

        if sent_count:
            email_content.is_sent = True
            email_content.date_sent = timezone.now()
            email_content.save(update_fields=["is_sent", "date_sent", "updated_at"])
        return sent_count

    @staticmethod
    def send_template_email(recipient_list, subject, template_path, context=None, from_email=None, queue=None):
        context = context or {}
        should_queue = EmailService._async_enabled() if queue is None else bool(queue)
        sender = from_email or settings.EMAIL_HOST_USER

        if should_queue:
            task = EmailService._queue_task(
                "send_email_task",
                recipient_list=list(recipient_list or []),
                subject=subject,
                template_path=template_path,
                context=context,
                from_email=sender,
            )
            if task is not None:
                return task

        html_message = render_to_string(template_path, context)
        plain_message = strip_tags(html_message)
        return EmailService._send_mail_recorded(
            subject, plain_message, html_message, recipient_list, sender
        )

    @staticmethod
    def send_subscription_notification(user, context, queue=None):
        should_queue = EmailService._async_enabled() if queue is None else bool(queue)
        if should_queue:
            task = EmailService._queue_task(
                "send_subscription_notification_task",
                user_id=user.id,
                context=context or {},
            )
            if task is not None:
                return task

        subject = "Confirmation de votre abonnement"
        html_message = render_to_string(
            "emails/subscription_confirmation.html",
            {
                "user": user,
                "site_url": settings.SITE_URL,
                **(context or {}),
            },
        )
        plain_message = strip_tags(html_message)
        return EmailService._send_mail_recorded(
            subject, plain_message, html_message, [user.email], settings.EMAIL_HOST_USER
        )

    @staticmethod
    def send_alert_notification(alert, queue=None):
        should_queue = EmailService._async_enabled() if queue is None else bool(queue)
        if should_queue:
            task = EmailService._queue_task("send_alert_notification_task", loss_alert_id=alert.id)
            if task is not None:
                return task

        subject = f"Nouvelle alerte de perte - {alert.name}"
        html_message = render_to_string(
            "emails/alert_notification.html",
            {
                "alert": alert,
                "site_url": settings.SITE_URL,
            },
        )
        plain_message = strip_tags(html_message)
        return EmailService._send_mail_recorded(
            subject, plain_message, html_message, [getattr(alert, "email", None)], settings.EMAIL_HOST_USER
        )

    @staticmethod
    def send_funding_request_notification(funding_request, queue=None):
        should_queue = EmailService._async_enabled() if queue is None else bool(queue)
        if should_queue:
            task = EmailService._queue_task(
                "send_funding_request_notification_task",
                funding_request_id=funding_request.id,
            )
            if task is not None:
                return task

        subject = f"Nouvelle demande de financement - {funding_request.title}"
        html_message = render_to_string(
            "emails/funding_request_notification.html",
            {
                "funding_request": funding_request,
                "site_url": settings.SITE_URL,
            },
        )
        plain_message = strip_tags(html_message)

        recipient = getattr(funding_request, "email", None)
        if not recipient and getattr(funding_request, "created_by", None):
            recipient = funding_request.created_by.email

        return EmailService._send_mail_recorded(
            subject, plain_message, html_message, [recipient], settings.EMAIL_HOST_USER
        )

    @staticmethod
    def send_donation_notification(donation, queue=None):
        should_queue = EmailService._async_enabled() if queue is None else bool(queue)
        if should_queue:
            task = EmailService._queue_task("send_donation_notification_task", donation_id=donation.id)
            if task is not None:
                return task

        subject = "Merci pour votre don!"
        html_message = render_to_string(
            "emails/donation_notification.html",
            {
                "donation": donation,
                "site_url": settings.SITE_URL,
            },
        )
        plain_message = strip_tags(html_message)
        sent = EmailService._send_mail_recorded(
            subject, plain_message, html_message, [donation.donor_email], settings.EMAIL_HOST_USER
        )

        if donation.funding_request:
            subject = "Vous avez recu un nouveau don!"
            html_message = render_to_string(
                "emails/donation_received_notification.html",
                {
                    "donation": donation,
                    "site_url": settings.SITE_URL,
                },
            )
            plain_message = strip_tags(html_message)
            sent += EmailService._send_mail_recorded(
                subject,
                plain_message,
                html_message,
                [donation.funding_request.email],
                settings.EMAIL_HOST_USER,
            )
        return sent

    @staticmethod
    def send_subscription_reminder(user, queue=None):
        should_queue = EmailService._async_enabled() if queue is None else bool(queue)
        if should_queue:
            task = EmailService._queue_task("send_subscription_reminder_task", user_id=user.id)
            if task is not None:
                return task

        subject = "Rappel d'abonnement"
        html_message = render_to_string(
            "emails/subscription_reminder.html",
            {
                "user": user,
                "site_url": settings.SITE_URL,
            },
        )
        plain_message = strip_tags(html_message)
        return EmailService._send_mail_recorded(
            subject, plain_message, html_message, [user.email], settings.EMAIL_HOST_USER
        )
