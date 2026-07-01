import logging
from django.dispatch import receiver
from django_djomy.signals import djomy_payment_success
from page.models import Donation, FundPayment

logger = logging.getLogger(__name__)

@receiver(djomy_payment_success)
def handle_djomy_payment_success(sender, reference, transaction_id, amount, **kwargs):
    """
    Écouteur du signal de succès de paiement Djomy.
    Met à jour les modèles Donation ou FundPayment en fonction de la référence.
    """
    logger.info(f"Traitement du signal de paiement pour la référence : {reference}")

    # Recherche dans Donation
    donation = Donation.objects.filter(reference=reference).first()
    if donation:
        if donation.status != 'réussi':
            donation.status = 'réussi'
            donation.transaction_id = transaction_id
            donation.save()
            logger.info(f"Donation {reference} marquée comme réussie via signal.")
        else:
            logger.info(f"Donation {reference} déjà marquée comme réussie. (Idempotence)")
        return

    # Recherche dans FundPayment (Financement)
    fund_payment = FundPayment.objects.filter(reference=reference).first()
    if fund_payment:
        if fund_payment.status != 'réussi':
            fund_payment.status = 'réussi'
            fund_payment.transaction_id = transaction_id
            fund_payment.save()
            
            # Mise à jour du montant reçu sur la demande de financement
            if fund_payment.funding_request:
                funding_request = fund_payment.funding_request
                funding_request.amount_received += fund_payment.amount
                funding_request.save()
                logger.info(f"FundPayment {reference} marqué comme réussi via signal. FundingRequest mise à jour.")
            else:
                logger.warning(f"FundPayment {reference} n'a pas de demande de financement associée.")
        else:
            logger.info(f"FundPayment {reference} déjà marqué comme réussi. (Idempotence)")
        return
    
    logger.warning(f"Référence de paiement {reference} introuvable dans Donation et FundPayment.")
