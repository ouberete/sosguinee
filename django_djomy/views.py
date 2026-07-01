from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .services import DjomyService
from .models import DjomyPayment
import json
import re
import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def djomy_webhook(request):
    """Webhook Djomy avec protection anti-rejeu (idempotence)."""
    service = DjomyService()
    signature = request.headers.get('X-Webhook-Signature')

    if not service.verify_webhook_signature(request.body, signature):
        logger.warning("Djomy Webhook: signature invalide rejetée.")
        return HttpResponse("Invalid Signature", status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)

    event_type = payload.get('eventType')
    data = payload.get('data', {})

    if event_type == "payment.success":
        ref = data.get('merchantPaymentReference', '')
        transaction_id = data.get('transactionId', '')
        amount = data.get('amount')

        # --- Idempotence : si déjà traité, on ignore ---
        if transaction_id and DjomyPayment.objects.filter(
            transaction_id=transaction_id, status='SUCCESS'
        ).exists():
            logger.info(f"Webhook doublon ignoré pour transaction {transaction_id}.")
            return JsonResponse({"status": "already_processed"})

        # 1. Mise à jour du modèle local DjomyPayment
        try:
            dj_pay = DjomyPayment.objects.get(merchant_reference=ref)
            dj_pay.transaction_id = transaction_id
            dj_pay.status = 'SUCCESS'
            dj_pay.raw_payload = payload
            dj_pay.save()
        except DjomyPayment.DoesNotExist:
            DjomyPayment.objects.create(
                merchant_reference=ref,
                transaction_id=transaction_id,
                amount=amount or 0,
                status='SUCCESS',
                raw_payload=payload,
            )

        # 2. Émission du signal pour informer les autres applications
        from .signals import djomy_payment_success
        djomy_payment_success.send(
            sender=DjomyPayment,
            reference=ref,
            transaction_id=transaction_id,
            amount=amount,
        )
        logger.info(f"Signal djomy_payment_success émis pour la référence {ref}.")

    return JsonResponse({"status": "received"})


@staff_member_required
def admin_liste_paiements(request):
    """Vue protégée pour lister les liens de paiement Djomy."""
    page = request.GET.get('page', '1')

    # --- Validation du paramètre page ---
    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    service = DjomyService()
    data = service.list_payment_links(page=page)

    local_payments = DjomyPayment.objects.all()[:50]

    return render(request, 'djomy/liste_liens.html', {
        'liens': data.get('items', []) if data else [],
        'pagination': data.get('paginationRequest') if data else None,
        'local_payments': local_payments,
        'api_error': data is None,
    })


# Regex stricte : alphanumérique, tirets, underscores
_TRANSACTION_ID_RE = re.compile(r'^[a-zA-Z0-9_-]{1,255}$')


@staff_member_required
def detail_transaction_check(request, transaction_id):
    """Vue protégée pour vérifier le statut d'une transaction."""
    # --- Validation du transaction_id ---
    if not _TRANSACTION_ID_RE.match(transaction_id):
        return render(request, 'djomy/detail_statut.html', {
            'status': None,
            'error': "Identifiant de transaction invalide.",
        })

    service = DjomyService()
    status_data = service.get_payment_status(transaction_id)

    return render(request, 'djomy/detail_statut.html', {
        'status': status_data,
    })
