import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def reconcile_pending_payments():
    """Réconcilie / expire les paiements restés en ``en_attente`` (point a).

    **Désactivé par défaut** : ne fait rien tant que
    ``PAYMENT_RECONCILIATION_ENABLED`` n'est pas à ``True``.

    Pour chaque ``Donation`` / ``FundPayment`` en attente plus vieux que
    ``PENDING_PAYMENT_EXPIRY_HOURS`` :
      - on revérifie le statut réel auprès de l'API Djomy ;
      - ``réussi``  -> confirmation idempotente (``_apply_payment_success``) ;
      - ``échoué``  -> ``_mark_payment_failed`` ;
      - sinon (statut non confirmé et paiement périmé) -> considéré abandonné,
        passé en ``échoué``.

    La confirmation reste protégée par le verrou en base de
    ``_apply_payment_success`` : aucun double crédit possible.
    """
    if not getattr(settings, "PAYMENT_RECONCILIATION_ENABLED", False):
        logger.debug("Réconciliation paiements désactivée (PAYMENT_RECONCILIATION_ENABLED=False).")
        return {"enabled": False}

    # Imports tardifs : évite tout souci d'ordre d'import au chargement Celery.
    from page.models import Donation, FundPayment
    from page.views import (
        _apply_payment_success,
        _mark_payment_failed,
        _verify_payment_status_with_djomy,
        _log_payment_event,
    )

    expiry_hours = int(getattr(settings, "PENDING_PAYMENT_EXPIRY_HOURS", 24))
    cutoff = timezone.now() - timedelta(hours=expiry_hours)

    counters = {"checked": 0, "succeeded": 0, "failed": 0, "expired": 0}

    for model in (Donation, FundPayment):
        stale = model.objects.filter(status="en_attente", created_at__lt=cutoff)
        for payment in stale.iterator():
            counters["checked"] += 1
            try:
                verified = _verify_payment_status_with_djomy(payment)
            except Exception as exc:
                logger.warning(
                    "Réconciliation: vérif Djomy échouée pour %s#%s: %s",
                    model.__name__, payment.pk, exc,
                )
                verified = None

            if verified == "réussi":
                _apply_payment_success(payment)
                counters["succeeded"] += 1
            elif verified == "échoué":
                _mark_payment_failed(payment)
                counters["failed"] += 1
            else:
                # Statut non confirmé au-delà du délai -> paiement abandonné.
                if _mark_payment_failed(payment):
                    counters["expired"] += 1

    _log_payment_event("payment_reconciliation_run", provider="djomy", **counters)
    logger.info("Réconciliation paiements: %s", counters)
    return counters
