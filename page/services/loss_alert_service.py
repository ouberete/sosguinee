import logging
from django.core.cache import cache
from page.models import LossAlertStatus, UserActionLog
from sosguinee.utils.email_service import EmailService

logger = logging.getLogger(__name__)

class LossAlertService:
    
    @staticmethod
    def create_loss_alert_from_form(request, form, identifier=None):
        """
        Crée une alerte de perte à partir d'un formulaire validé, enregistre les documents optionnels,
        historise l'action, et envoie un email de notification.
        Retourne l'alerte créée.
        """
        loss_alert = form.save()
        docs = request.FILES.getlist('optional_docs')
        if docs:
            loss_alert.add_docs(docs)
            
        # Get first loss alert status "En cours"
        lost_alert_status = LossAlertStatus.objects.filter(name="En cours").first()
        loss_alert.loss_alert_status_id = lost_alert_status.id if lost_alert_status else None
        loss_alert.save()   
        
        # Enregistrement du log utilisateur
        UserActionLog.record(
            request=request,
            action=UserActionLog.ACTION_CREATE,
            obj=loss_alert,
            metadata={'status': loss_alert.status_alert_name},
        )
        
        # Envoi de l'email de confirmation. Un échec ne concerne pas
        # l'utilisateur (l'alerte est bien enregistrée) : on le journalise
        # seulement, sans message d'erreur à l'écran.
        try:
            EmailService.send_alert_notification(loss_alert)
        except Exception as e:
            logger.warning("Email alerte non envoye (alerte conservee): %s", e, exc_info=True)

        return loss_alert
