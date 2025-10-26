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

@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, 'accounts/subscription/plans.html', {'plans': plans})

@login_required
def subscribe(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Plan non trouvé'}, status=404)
        
        # Créer un paiement
        payment = SubscriptionPayment.objects.create(
            user=request.user,
            plan=plan,
            amount=plan.price,
            transaction_id=str(uuid.uuid4())
        )
        
        # Ici, intégrer la logique de paiement avec PayCard
        # Pour l'exemple, on considère le paiement comme réussi
        payment.status = 'completed'
        payment.save()
        
        with transaction.atomic():
            # Mettre à jour ou créer l'abonnement
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
            'days_remaining': subscription.days_remaining()
        }
        return JsonResponse(data)
    except ObjectDoesNotExist:
        return JsonResponse({
            'is_active': False,
            'message': 'Aucun abonnement trouvé'
        })