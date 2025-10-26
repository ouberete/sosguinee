from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from page.models import LossAlert, FundingRequest, Donation

@login_required
def profile(request):
    # Récupérer les alertes, demandes de financement et dons de l'utilisateur
    alerts = LossAlert.objects.filter(user=request.user).order_by('-created_at')
    funding_requests = FundingRequest.objects.filter(user=request.user).order_by('-created_at')
    donations = Donation.objects.filter(donor_email=request.user.email).order_by('-created_at')

    context = {
        'alerts': alerts,
        'funding_requests': funding_requests,
        'donations': donations
    }
    
    return render(request, 'accounts/profile.html', context)