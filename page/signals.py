import logging
from decimal import Decimal, InvalidOperation
from django.dispatch import receiver
from django_djomy.signals import djomy_payment_success
from page.models import Donation, FundPayment

logger = logging.getLogger(__name__)


@receiver(djomy_payment_success)
def handle_djomy_payment_success(sender, reference, transaction_id, amount, **kwargs):
    """
    Écouteur du signal de succès de paiement Djomy (émis par le webhook de
    django_djomy). La confirmation est déléguée à
    ``page.views._apply_payment_success`` pour appliquer EXACTEMENT la même
    logique idempotente que le webhook principal (verrou en base, crédit du
    financement, clôture éventuelle de la collecte, email de confirmation) —
    quel que soit l'endpoint webhook réellement appelé par Djomy.
    """
    # Import tardif: page.views importe de nombreux modules; un import au niveau
    # module créerait une dépendance circulaire au chargement des signaux.
    from page.views import _apply_payment_success

    payment = (
        Donation.objects.filter(reference=reference).first()
        or FundPayment.objects.filter(reference=reference).first()
    )
    if payment is None:
        logger.warning(
            "Référence de paiement %s introuvable dans Donation et FundPayment.",
            reference,
        )
        return

    try:
        received_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        received_amount = None
    if received_amount != payment.amount:
        logger.warning(
            "Confirmation Djomy ignorée: montant manquant ou différent pour la référence %s.",
            reference,
        )
        return

    if transaction_id and not payment.transaction_id:
        payment.transaction_id = transaction_id
        payment.save(update_fields=["transaction_id", "updated_at"])

    _apply_payment_success(payment)
