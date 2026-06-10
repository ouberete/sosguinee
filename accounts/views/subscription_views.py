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
        plan_id = request.POST.get('plan_id')
        plan_public_id = request.POST.get('plan_public_id')
        
        try:
            plan = SubscriptionPlan.objects.get(public_id=plan_public_id) if plan_public_id else SubscriptionPlan.objects.get(id=plan_id)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Plan non trouvÃ©'}, status=404)
        
        # CrÃ©er un paiement
        payment = SubscriptionPayment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            transaction_id=str(uuid.uuid4())
        )
        
        # Ici, intÃ©grer la logique de paiement avec PayCard
        # Pour l'exemple, on considÃ¨re le paiement comme rÃ©ussi
        payment.status = 'completed'
        payment.save()
        
        with transaction.atomic():
            # Mettre Ã  jour ou crÃ©er l'abonnement
            subscription, created = UserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'start_date': timezone.now(),
                    'is_active': True,
                    'reminder_sent': False
                }
            )
            
            try:
                # Envoyer un email de confirmation
                context = {
                    'plan_name': plan.name,
                    'end_date': subscription.end_date,
                }
                EmailService.send_subscription_notification(request.user, context)
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'email: {e}")
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'MÃ©thode non autorisÃ©e'}, status=405)

@login_required
def cancel_subscription(request):
    if request.method == 'POST':
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            subscription.is_active = False
            subscription.save()
            
            messages.success(request, "Votre abonnement a Ã©tÃ© annulÃ© avec succÃ¨s.")
            return JsonResponse({'success': True})
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Aucun abonnement actif'}, status=404)
    
    return JsonResponse({'error': 'MÃ©thode non autorisÃ©e'}, status=405)

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

