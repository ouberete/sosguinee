import logging
from django.contrib import messages
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
        
        # Envoi de l'email
        try:
            EmailService.send_alert_notification(loss_alert)
        except Exception as e:
            logger.warning("Email alerte non envoye (alerte conservee): %s", e, exc_info=True)
            messages.error(request, "L'envoi du mail a échoué. Votre alerte a bien été enregistrée.")
        else:
            if identifier:
                # Supprimer le rate limit cache key, note : on a besoin de recréer la clé ou que la vue s'en occupe.
                # Dans ce cas, la vue passera la clé cache ou l'identifier directement.
                pass
                
        return loss_alert
