import logging
from decimal import Decimal, InvalidOperation
from django.dispatch import receiver
from django_djomy.signals import djomy_payment_success
from page.models import Donation, FundPayment

logger = logging.getLogger(__name__)


@receiver(djomy_payment_success)
def handle_djomy_payment_success(
    sender,
    reference,
    transaction_id,
    amount,
    received_amount,
    fees,
    payment_method="",
    currency="GNF",
    **kwargs,
):
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
        paid_amount = Decimal(str(amount))
        received_amount = Decimal(str(received_amount))
        fees = Decimal(str(fees))
    except (InvalidOperation, TypeError, ValueError):
        return
    if (
        paid_amount != payment.amount
        or received_amount < 0
        or fees < 0
        or received_amount + fees != paid_amount
        or str(currency).strip().upper() != "GNF"
    ):
        logger.warning(
            "Confirmation Djomy ignorée: comptabilité invalide pour la référence %s.",
            reference,
        )
        return

    payment.received_amount = received_amount
    payment.fees = fees
    payment.provider_payment_method = str(payment_method or "")[:32]
    payment.provider_currency = str(currency).strip().upper()
    if transaction_id:
        payment.provider_transaction_id = transaction_id
    payment.save(update_fields=[
        "received_amount",
        "fees",
        "provider_payment_method",
        "provider_currency",
        "provider_transaction_id",
        "updated_at",
    ])

    _apply_payment_success(payment)
