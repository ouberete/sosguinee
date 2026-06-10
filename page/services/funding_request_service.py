import logging
from django.contrib import messages
from page.models import FundingRequestStatus, UserActionLog
from sosguinee.utils.email_service import EmailService

logger = logging.getLogger(__name__)

class FundingRequestService:

    @staticmethod
    def create_funding_request_from_form(request, form, identifier=None):
        """
        Crée une demande de financement à partir d'un formulaire validé, enregistre les documents,
        historise l'action, et envoie un email de notification.
        """
        funding_request = form.save()
        docs = request.FILES.getlist('optional_docs')
        if docs:
            funding_request.add_funding_docs(docs)
            
        funding_request_status = FundingRequestStatus.objects.filter(name="En cours").first()
        funding_request.funding_request_status_id = funding_request_status.id if funding_request_status else None
        funding_request.save()
        
        UserActionLog.record(
            request=request,
            action=UserActionLog.ACTION_CREATE,
            obj=funding_request,
            metadata={'status': funding_request.funding_request_status_name},
        )
        
        try:
            EmailService.send_funding_request_notification(funding_request)
        except Exception as e:
            logger.warning("Email demande de financement non envoye (demande conservee): %s", e, exc_info=True)
            messages.error(request, "L'envoi du mail a échoué. Votre demande a bien été enregistrée.")
        
        return funding_request
