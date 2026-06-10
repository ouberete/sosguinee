from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from .services import DjomyService
from .models import DjomyPayment
import json
import logging
from datetime import datetime
logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def djomy_webhook(request):
    service = DjomyService()
    signature = request.headers.get('X-Webhook-Signature')
    logger.info(f"Signature reçue : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if not service.verify_webhook_signature(request.body, signature):
        logger.warning("Invalid Djomy Webhook Signature")
        return HttpResponse("Invalid Signature", status=401)
    
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)

    event_type = payload.get('eventType')
    data = payload.get('data', {})
    
    if event_type == "payment.success":
        ref = data.get('merchantPaymentReference')
        transaction_id = data.get('transactionId')
        amount = data.get('amount')
        
        # 1. Mise à jour du modèle local DjomyPayment
        try:
            dj_pay = DjomyPayment.objects.get(merchant_reference=ref)
            dj_pay.transaction_id = transaction_id
            dj_pay.status = 'SUCCESS'
            dj_pay.raw_payload = payload
            dj_pay.save()
        except DjomyPayment.DoesNotExist:
            # Si non trouvé, on le crée
            DjomyPayment.objects.create(
                merchant_reference=ref,
                transaction_id=transaction_id,
                amount=amount,
                status='SUCCESS',
                raw_payload=payload
            )

        # 2. Émission du signal pour informer les autres applications
        from .signals import djomy_payment_success
        djomy_payment_success.send(
            sender=DjomyPayment,
            reference=ref,
            transaction_id=transaction_id,
            amount=amount
        )
        logger.info(f"Signal djomy_payment_success émis pour la référence {ref}.")
                
    return JsonResponse({"status": "received"})

def admin_liste_paiements(request):
    """Vue pour afficher l'historique Djomy dans l'interface admin"""
    service = DjomyService()
    page = request.GET.get('page', 1)
    
    data = service.list_payment_links(page=page)
    
    # On récupère aussi nos enregistrements locaux pour comparaison
    local_payments = DjomyPayment.objects.all()[:50]
    
    return render(request, 'djomy/liste_liens.html', {
        'liens': data.get('items', []) if data else [],
        'pagination': data.get('paginationRequest') if data else None,
        'local_payments': local_payments
    })

def detail_transaction_check(request, transaction_id):
    """Vue pour forcer la vérification d'un statut via l'API Djomy"""
    service = DjomyService()
    status_data = service.get_payment_status(transaction_id)
    
    # Si le statut est SUCCESS dans l'API, on peut synchroniser localement si besoin
    if status_data and status_data.get('status') == 'SUCCESS':
        ref = status_data.get('merchantPaymentReference')
        # On pourrait déclencher la même logique que le webhook ici
        
    return render(request, 'djomy/detail_statut.html', {
        'status': status_data
    })
