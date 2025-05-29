import uuid
from smtplib import SMTPException
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth import get_user_model
from page.models import FundingRequest, LossAlert, FundingType, LossAlertType, LossAlertStatus, FundingRequestStatus, \
    Donation
from page.forms import  DonationForm, FundingRequestForm, LossAlertForm, MessageContactForm
from django.core.paginator import Paginator
from page.models import UserDetails
from sosguinee.utils.sending_email import Utilities

User = get_user_model()
#Add new user
def index(request):
    funding_requests= FundingRequest.objects.order_by("-created_at")[:6]
    loss_alerts = LossAlert.objects.order_by("-created_at")[:6]
    return render(request, 'page/index.html', {'funding_requests': funding_requests, 'loss_alerts': loss_alerts})


def funding_request_list(request):
    funding_request_types = FundingType.objects.all()
    funding_request_statuses = FundingRequestStatus.objects.all().exclude(name="Clos").exclude(name="Trouvé")
                
    return render(request, 'page/funding_requests.html', {'funding_request_types': funding_request_types, 'funding_request_statuses': funding_request_statuses})

def loss_alert_list(request):
    loss_alert_types = LossAlertType.objects.all()
    loss_alert_statuses = LossAlertStatus.objects.all().exclude(name="Clos").exclude(name="Trouvé")
    return render(request, 'page/loss_alerts.html', {'loss_alert_types': loss_alert_types, 'loss_alert_statuses': loss_alert_statuses})

def add_funding_request(request):
    
    print("add_funding_request")
    if request.method == 'POST':
        print("add_funding_request POST")
        form = FundingRequestForm(request.POST, request.FILES)
        if form.is_valid():
            print("add_funding_request valid")
            fundingRequest = form.save()
            docs = request.FILES.getlist('optional_docs')
            fundingRequest.add_docs(docs)
            fundingRequest.funding_request_status_id = 1
            fundingRequest.save()
            
            #'beneficiary_name', 'description_needs', 'country', 'city',
            # 'quarter', 'address', 'funding_request_type', 'funding_request_status',
            # 'funding_amount', 'email', 'phone', 'principal_image'
            
            context = {
                'name': fundingRequest.beneficiary_name,
                'type': fundingRequest.funding_request_type.name,
                'description': fundingRequest.description_needs,
                'email': fundingRequest.email,
                'phone': fundingRequest.phone,
                'country': fundingRequest.country,
                'city': fundingRequest.city,
                'quarter': fundingRequest.quarter,
                'address': fundingRequest.address,
                'amount': fundingRequest.funding_amount,
                'email': fundingRequest.email,
                'phone': fundingRequest.phone,
                'city': fundingRequest.city,    
            }
            email_template ='page/template_email/add_funding_request_email.html'
            to_email = [fundingRequest.email,]
            email_subject = 'Demande de financement'
            
            try:
                print("sending email")
                Utilities.sending_email(to_email, email_subject, email_template, context)
                print("email sent")
            except SMTPException as e:
                print(e)
                return render(request, 'page/add_funding_request.html', {'error': 'L\'envoi du mail a été echoué. Veuillez contacter l\'administrateur.'})
            
            
            return render(request,'page/confirmation_page/confirmation_funding_request_added.html', {'request':'added'})
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
            docs = request.FILES.getlist('optional_docs')
            lossAlert.add_docs(docs)
            lossAlert.loss_alert_status_id = 1
            lossAlert.save()   
            
            email_template ='page/template_email/add_loss_alert_email.html'
            
            to_email = [lossAlert.email,]
            email_subject = 'Ajout alerte'
            context = {
                    'name': lossAlert.name,
                    'type': lossAlert.loss_alert_type.name,
                    'description': lossAlert.description,
                    'email': lossAlert.email,
                    'phone': lossAlert.phone,
                    'country': lossAlert.country,
                    'city': lossAlert.city,
                    'quarter': lossAlert.quarter,
                    'address': lossAlert.address,
                    'date_alert': lossAlert.date_alert,
                    'hour_alert': lossAlert.hour_alert
                }
                        
            try:
                print("sending email")
                Utilities.sending_email(to_email, email_subject, email_template, context)
                print("email sent")
            except SMTPException as e:
                print("email not sent", e)
                return render(request, 'page/add_loss_alert.html', {'form': form, 'error': 'L\'envoi du mail a échoué. Veuillez contacter l\'administrateur.'}) 
          
            return render(request, 'page/confirmation_page/confirmation_loss_alert_added.html',{'request': 'added'} )
        else:
            print("add_loss_alert not valid")
            #Print errors
            errors = form.errors
            print(errors)
            return render(request, 'page/add_loss_alert.html', {'form': form})
    else:
        print("add_loss_alert GET")
        form = LossAlertForm()
    return render(request, 'page/add_loss_alert.html', {'form': form})

def funding_request_detail(request, pk):
    funding_request = FundingRequest.objects.get(pk=pk)
    
    return render(request, 'page/funding_request_details.html', {'funding_request': funding_request})

def loss_alert_detail(request, pk):
    alert = LossAlert.objects.get(pk=pk)
    #alert = LossAlert()
    return render(request, 'page/loss_alert_details.html', {'alert': alert})

def contact(request):
    contact = MessageContactForm()
    if request.method == 'POST':
        print(request.POST)
        name = request.POST.get('name') 
        email = request.POST.get('email')
        message = request.POST.get('message')
        contact = MessageContactForm(request.POST)
        if contact.is_valid():
            contact.save()
            #Send Message contact email
            context = {
                'name': name,
                'email': email,
                'message': message
            }
            
            template_email = 'page/template_email/contact_form_email.html'
            to_email = "komoro@gyopmail.com"
            mail_subject = "Message de contact"
            try:
                print("sending email")
                Utilities.sending_email([to_email, email], mail_subject, template_email, context)
                print("email sent")
            except SMTPException as e:
                print("email not sent", e)
                return render(request, 'page/contact.html', {'error': 'L\'envoi du mail a échoué. Veuillez contacter l\'administrateur.'})
            contact = MessageContactForm()
            return render(request, 'page/contact.html', {'success': 'Le message a été envoyé avec succès.', 'form': contact})
        else :
            return render(request, 'page/contact.html', {'form': contact})
    return render(request, 'page/contact.html', {'form': contact})

def thanks(request):
    return render(request, 'page/thanks.html')


def donation(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        method = request.POST.get('method')
        reference = str(uuid.uuid4())

        user = request.user if request.user.is_authenticated else None

        if not user:
            email = request.POST.get('email')
            phone = request.POST.get('phone')

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                username = email or phone or f"user_{uuid.uuid4().hex[:8]}"
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=request.POST.get('first_name', ''),
                    last_name=request.POST.get('last_name', '')
                )
                user.save()

                # Créer ou mettre à jour le profil avec le téléphone
                UserDetails.objects.update_or_create(
                    user=user,
                    defaults={'phone': phone}
                )

        else:
            # Si connecté, tu peux mettre à jour le profil aussi si besoin
            phone = request.POST.get('phone')
            if phone:
                UserDetails.objects.update_or_create(
                    user=user,
                    defaults={'phone': phone}
                )

        # Enregistrer le don
        Donation.objects.create(
            amount=amount,
            method=method,
            status='en_attente',
            user=user,
            reference=reference
        )

        return redirect('donation_thanks')

    return render(request, 'page/donation.html')
def messageContact(request):
    if request.method == 'POST':
        print(request.POST)
        name = request.POST.get('name') 
        email = request.POST.get('email')
        message = request.POST.get('message')
        contact = MessageContactForm(request.POST)
        if contact.is_valid():
            contact.save()
            #Send Message contact email
            context = {
                'name': name,
                'email': email,
                'message': message
            }
            
            to_email = "yuss@yopmail.com"
            mail_subject = "Message de contact"
            template_email = 'page/template_email/contact_form_email.html'
            try:
                print("sending email")
                
                Utilities.sending_email([to_email, email], mail_subject, template_email, context)
                
                
                print("email sent")
            except SMTPException as e:
                print("email not sent", e)
                return JsonResponse({'error': 'L\'envoi du mail a échoué. Veuillez contacter l\'administrateur.'})
            return JsonResponse( {'success': 'Le message a été envoyé.'})
        else :
            errors = contact.errors
            print("Errors: ",errors)
            return JsonResponse({'error': "Veuillez remplir tous les champs.", 'errors': errors})
    return JsonResponse({'error': 'Veuillez remplir tous les champs.'})

def confirmation_loss_alert_added(request):
    return render(request, 'page/confirmation_page/confirmation_loss_alert_added.html')

def confirmation_funding_request_added(request):
    return render(request, 'page/confirmation_page/confirmation_funding_request_added.html')


def help_support(request):
    return render(request, 'page/help_policy/help_support.html')

def policy_privacy(request):
    return render(request, 'page/help_policy/policy_privacy.html')

def about(request):
    return render(request, 'page/about.html')




#Api url view
class FundingRequestListView(View):
    def get(self, request):
        
        # Récupère les filtres à partir des paramètres GET
        status = request.GET.get('status')
        funding_type = request.GET.get('funding_type')
        min_amount = request.GET.get('min_amount')
        max_amount = request.GET.get('max_amount')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        beneficiary_name = request.GET.get('beneficiary_name')
        
        funding_list = FundingRequest.objects.all()  # Récupère tous les éléments
        
         # Applique les filtres dynamiques
        if status:
            funding_list = funding_list.filter(funding_request_status__name=status)
        if funding_type:
            funding_list = funding_list.filter(funding_request_type__name=funding_type)
        if min_amount:
            funding_list = funding_list.filter(funding_amount__gte=min_amount)
        if max_amount:
            funding_list = funding_list.filter(funding_amount__lte=max_amount)
        if start_date:
            funding_list = funding_list.filter(start_date__gte=start_date)
        if end_date:
            funding_list = funding_list.filter(end_date__lte=end_date)
        if beneficiary_name:
            funding_list = funding_list.filter(beneficiary_name__icontains=beneficiary_name)
            
        page_number = request.GET.get('page', 1)  # Numéro de la page à partir des paramètres GET, par défaut 1
        items_per_page = request.GET.get('items_per_page', 10)  # Nombre d'éléments par page, par défaut 10

        # Création du paginator
        paginator = Paginator(funding_list, items_per_page)
        try:
            page_obj = paginator.page(page_number)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        # Prépare les données pour le format JSON
        data = {
            'funding_requests': [
                {
                    'title': element.title,
                    'beneficiary_name': element.beneficiary_name,
                    'funding_request_status': element.funding_request_status_name,  # Utilise la propriété funding_request_status_name
                    'principal_image_url': element.principal_image.url if element.principal_image else '', 
                    'id': element.id,
                    'progress': element.progress,  # Utilise la propriété progress
                    'days_remaining': element.days_remaining,  # Utilise la propriété days_remaining
                    'amount': element.funding_amount,
                    'details_url': "/funding-request-details/"+str(element.id)+"/",          
                }
                for element in page_obj
            ],
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_elements': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        }

        return JsonResponse(data, safe=False)
    
    
class LossAlertListView(View):
    def get(self, request):
        
        # Récupère les filtres à partir des paramètres GET
        status = request.GET.get('status')
        type_alert = request.GET.get('type_alert')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        name = request.GET.get('name')

        # Récupère tous les éléments
        alert_list = LossAlert.objects.all()

        # Applique les filtres dynamiques
        if status:
            alert_list = alert_list.filter(loss_alert_status__name=status)
        if type_alert:
            alert_list = alert_list.filter(loss_alert_type__name=type_alert)
        if start_date:
            alert_list = alert_list.filter(date_alert__gte=start_date)
        if end_date:
            alert_list = alert_list.filter(date_alert__lte=end_date)
        if name:
            alert_list = alert_list.filter(name__icontains=name)

        page_number = request.GET.get('page', 1)  # Numéro de la page à partir des paramètres GET, par défaut 1
        items_per_page = request.GET.get('items_per_page', 9)  # Nombre d'éléments par page, par défaut 9

        # Création du paginator
        paginator = Paginator(alert_list, items_per_page)
        try:
            page_obj = paginator.page(page_number)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        # Prépare les données pour le format JSON
        data = {
            'loss_alerts': [
                {
                    'name': element.name,
                    'status_alert_name': element.status_alert_name,  # Utilise la propriété status_alert_name
                    'principal_image_url': element.principal_image.url if element.principal_image else '', 
                    'type_alert_name': element.type_alert_name,  # Utilise la propriété type_alert_name
                    'date_alert': element.date_alert,
                    'hour_alert': element.hour_alert,
                    'id': element.id,
                    'details_url': "/loss-alert-details/"+str(element.id)+"/",  # URL des détails de l'alerte
                }
                for element in page_obj
            ],
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_elements': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        }

        return JsonResponse(data, safe=False)


def donation_thanks(request):
    return render(request, 'page/donation_thanks.html')