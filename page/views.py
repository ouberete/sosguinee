from django.shortcuts import redirect, render
from page.models import FundingRequest, LossAlert, OptionalAlertImage
from page.forms import FundingRequestForm, LossAlertForm
from sosguinee import settings
# Create your views here.

#Add new user
def index(request):
    return render(request, 'page/index.html')


def funding_request_list(request):
    requests = FundingRequest.objects.all()
    return render(request, 'page/funding_requests.html', {'requests': requests})

def loss_alert_list(request):
    alerts = LossAlert.objects.all()
    return render(request, 'page/loss_alerts.html', {'alerts': alerts})

def add_funding_request(request):
    print("add_funding_request")
    if request.method == 'POST':
        print("add_funding_request POST")
        form = FundingRequestForm(request.POST, request.FILES)
        if form.is_valid():
            print("add_funding_request valid")
            fundingRequest = form.save()
            images = request.FILES.getlist('optional_images')
            fundingRequest.add_images(images)
            fundingRequest.save()
            return redirect("page/funding_requests")
        else:
            print("add_funding_request not valid")
            errors = form.errors
            return render(request, 'page/add_funding_request.html', {'form': form, 'errors': errors})
    else:
        print("add_funding_request GET")
        form = FundingRequestForm()
    return render(request, 'page/add_funding_request.html', {'form': form})

def add_loss_alert(request):
    print("add_loss_alert")
    if request.method == 'POST':
        print("add_loss_alert POST")
        form = LossAlertForm(request.POST, request.FILES)
        if form.is_valid():
            print("add_loss_alert valid")
            lossAlert = form.save()
            images = request.FILES.getlist('optional_images')
            lossAlert.add_images(images)
            lossAlert.save()                
            return redirect('page/loss-alerts')
        else:
            print("add_loss_alert not valid")
            return render(request, 'page/add_loss_alert.html', {'form': form})
    else:
        print("add_loss_alert GET")
        form = LossAlertForm()
    return render(request, 'page/add_loss_alert.html', {'form': form})

def funding_request_detail(request, pk):
    #request = FundingRequest.objects.get(pk=pk)
    request = FundingRequest()
    return render(request, 'page/funding_request_detail.html', {'request': request})

def loss_alert_detail(request, pk):
    #alert = LossAlert.objects.get(pk=pk)
    alert = LossAlert()
    return render(request, 'page/loss_alert_detail.html', {'alert': alert})

def contact(request):
    return render(request, 'page/contact.html')

def thanks(request):
    return render(request, 'page/thanks.html')


def donation(request):
    if request.method == 'POST':
        montant = request.POST.get('montant')
        autre_montant = request.POST.get('autre_montant')
        montant = autre_montant if montant == 'autre' else montant

        # Préparer les données pour PAYCARD
        data = {
            'amount': montant,
            'currency': 'GNF',
            'description': 'Donation',
            'api_key': settings.PAYCARD_API_KEY,
            'api_secret': settings.PAYCARD_API_SECRET,
            # Ajoutez d'autres paramètres requis par PAYCARD
        }

        # Faire une requête POST à PAYCARD
        response = request.post(settings.PAYCARD_ENDPOINT, data=data)
        if response.status_code == 200:
            return redirect('thanks')  # Rediriger vers une page de remerciement après le paiement réussi
        else:
            return render(request, 'page/donation.html', {'error': 'Le paiement a échoué. Veuillez réessayer.'})
    
    return render(request, 'page/donation.html')