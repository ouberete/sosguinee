from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.contrib import messages
from ..models.subscription import SubscriptionPlan, UserSubscription, SubscriptionPayment
from sosguinee.utils.email_service import EmailService
import uuid
from django.views.decorators.http import require_GET

@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'accounts/subscription/plans.html', {'plans': plans})

@login_required
def subscribe(request):
    if request.method == 'POST':
        # Désactivé tant qu'un paiement réel (Djomy) n'est pas branché sur ce
        # flux: l'ancienne version marquait le paiement 'completed' sans
        # aucune transaction, ce qui revenait à offrir les abonnements.
        return JsonResponse(
            {'error': "La souscription en ligne n'est pas encore disponible. Veuillez nous contacter."},
            status=503,
        )

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def cancel_subscription(request):
    if request.method == 'POST':
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            subscription.is_active = False
            subscription.save()
            
            messages.success(request, "Votre abonnement a été annulé avec succès.")
            return JsonResponse({'success': True})
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Aucun abonnement actif'}, status=404)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def subscription_status(request):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
        data = {
            'is_active': subscription.is_active,
            'plan_name': subscription.plan.name,
            'end_date': subscription.end_date.isoformat(),
            'days_remaining': subscription.days_remaining(),
            'subscription_public_id': str(subscription.public_id),
            'plan_public_id': str(subscription.plan.public_id) if subscription.plan else None
        }
        return JsonResponse(data)
    except ObjectDoesNotExist:
        return JsonResponse({'is_active': False, 'message': 'Aucun abonnement trouvé'})





@login_required
@require_GET
def plan_detail_by_public_id(request, public_id):
    try:
        plan = SubscriptionPlan.objects.get(public_id=public_id)
        data = {
            'public_id': str(plan.public_id),
            'name': plan.name,
            'price': float(plan.price),
            'duration_days': plan.duration_days,
            'features': plan.features,
            'created_at': plan.created_at.isoformat(),
        }
        return JsonResponse(data)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Plan non trouvé'}, status=404)


@login_required
@require_GET
def payment_detail_by_public_id(request, public_id):
    try:
        payment = SubscriptionPayment.objects.get(public_id=public_id, user=request.user)
        data = {
            'public_id': str(payment.public_id),
            'status': payment.status,
            'amount': float(payment.amount),
            'transaction_id': payment.transaction_id,
            'plan_public_id': str(payment.plan.public_id) if payment.plan else None,
            'payment_date': payment.payment_date.isoformat(),
        }
        return JsonResponse(data)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Paiement introuvable'}, status=404)

