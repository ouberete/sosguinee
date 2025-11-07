import uuid
from smtplib import SMTPException

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST

from page.models import FundingRequest, LossAlert, FundingType, LossAlertType, LossAlertStatus, FundingRequestStatus, \
    Donation, FundPayment, Comment
from page.forms import DonationForm, FundingRequestForm, LossAlertForm, MessageContactForm, FundingPaymentForm, \
    CommentForm
from django.core.paginator import Paginator
from page.models import UserDetails
from sosguinee.utils.email_service import EmailService
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.contrib import messages
import requests
from requests.exceptions import RequestException
User = get_user_model()
#Add new user
def index(request):
    funding_requests= FundingRequest.objects.order_by("-created_at")[:6]
    loss_alerts = LossAlert.objects.order_by("-created_at")[:6]
    funding_requests_count = FundingRequest.objects.count()
    loss_alerts_count = LossAlert.objects.count()

    return render(request, 'page/index.html', {'funding_requests': funding_requests, 'loss_alerts': loss_alerts,
                                               'funding_requests_count':funding_requests_count, 'loss_alerts_count':loss_alerts_count,
                                               'total_impact': loss_alerts_count + funding_requests_count})


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
            fundingRequest.add_funding_docs(docs)
            funding_request_status = FundingRequestStatus.objects.filter(name="En cours").first()
            fundingRequest.funding_request_status_id = funding_request_status.id if funding_request_status else None
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
                # Envoyer l'email avec le nouveau service
                EmailService.send_funding_request_notification(fundingRequest)
            except Exception as e:
                print("Erreur d'envoi d'email:", e)
                messages.error(request, 'L\'envoi du mail a échoué. Votre demande a bien été enregistrée.')
            
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
            #Get first lost alert status

            lost_alert_status = LossAlertStatus.objects.filter(name="En cours").first()
            lossAlert.loss_alert_status_id = lost_alert_status.id if lost_alert_status else None
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
                # Envoyer l'email avec le nouveau service
                EmailService.send_alert_notification(lossAlert)
            except Exception as e:
                print("Erreur d'envoi d'email:", e)
                messages.error(request, 'L\'envoi du mail a échoué. Votre alerte a bien été enregistrée.')
          
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

def funding_request_detail(request, pk=None, public_id=None):
    if pk is not None:
        funding_request = get_object_or_404(FundingRequest, pk=pk)
        return redirect('funding_request_details_public', public_id=funding_request.public_id, permanent=True)
    else:
        funding_request = get_object_or_404(FundingRequest, public_id=public_id)

    # Obtenir tous les commentaires liés à cet objet
    content_type = ContentType.objects.get_for_model(FundingRequest)
    comments = Comment.objects.filter(content_type=content_type, object_id=funding_request.id).select_related('user')

    comment_form = CommentForm()

    return render(request, 'page/funding_request_details.html', {
        'funding_request': funding_request,
        'comments': comments,  # 🔴 Important !
        'comment_form': comment_form,
        'model_name': 'fundingrequest',
        'object_id': funding_request.id
    })

def loss_alert_detail(request, pk=None, public_id=None):
    #alert = LossAlert()
    if pk is not None:
        alert = get_object_or_404(LossAlert, pk=pk)
        return redirect('loss_alert_detail_public', public_id=alert.public_id, permanent=True)
    else:
        alert = get_object_or_404(LossAlert, public_id=public_id)

    # Obtenir tous les commentaires liés à cet objet
    content_type = ContentType.objects.get_for_model(LossAlert)
    comments = Comment.objects.filter(content_type=content_type, object_id=alert.id, isDeleted=False).select_related('user')

    comment_form = CommentForm()

    return render(request, 'page/loss_alert_details.html', {
        'alert': alert,
        'comments': comments,  # 🔴 Important !
        'comment_form': comment_form,
        'model_name': 'lossalert',
        'object_id': alert.id
    })

def contact(request):
    contact = MessageContactForm(request.POST or None)
    if request.method == 'POST':
        print(request.POST)
        name = request.POST.get('name') 
        email = request.POST.get('email')
        message = request.POST.get('message')
        if contact.is_valid():
            contact.save()
            #Send Message contact email
            context = {
                'name': name,
                'email': email,
                'message': message
            }
            
            template_email = 'page/template_email/contact_form_email.html'
            to_email = [email,]
            mail_subject = "Message de contact"
            try:
                print("sending email")
                EmailService.send_template_email(to_email, mail_subject, template_email, context)
                print("email sent")
            except Exception as e:
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
    form = DonationForm(request.POST or None)
    if request.method == 'POST':
        print("Donation POST request received")
        if not form.is_valid():
            print("Donation form is not valid")
            errors = form.errors
            print(errors)
            return render(request, 'page/donation.html', {'form': form, 'errors': errors})
        print("Donation form is valid")
        # Récupérer les données du formulaire

        amount = form.cleaned_data['amount']
        user_email = form.cleaned_data['donor_email']
        donor_first_name = form.cleaned_data['donor_first_name']
        donor_last_name = form.cleaned_data['donor_last_name']
        donor_country = form.cleaned_data['donor_country']
        donor_city = form.cleaned_data['donor_city']
        donor_phone = form.cleaned_data['donor_phone']
        donor_address = form.cleaned_data['donor_address']
        try:
            # Enregistrer le paiement dans la base de données
            payment = Donation.objects.create(
                amount=amount,
                donor_email=user_email,
                donor_first_name= donor_first_name,
                donor_last_name= donor_last_name,
                donor_address= donor_address,
                donor_city=donor_city,
                donor_country=donor_country,
                donor_phone =donor_phone,
                transaction_id=str(uuid.uuid4()),  # Générer un ID de transaction unique
                #reference=data.get('reference')
            )

            # payload = {
            #     "public_key": settings.PAYCARD_API_KEY,
            #     "amount": int(amount),
            #     "currency": "GNF",
            #     "email": user_email,
            #     "description": f"Financement demande #{funding_id}",
            #     "callback_url": request.build_absolute_uri(
            #         reverse('paycard_payment_callback', kwargs={'payment_id': payment.id, 'type': 'Don'})
            #     )
            #     }
            #
            # response = requests.post(settings.PAYCARD_ENDPOINT, json=payload, timeout=10)
            #
            # if response.status_code != 200:
            #     messages.error(request, "Erreur de communication avec PayCard.")
            #     return  render(request, 'page/donation.html', { 'form': form})
            #
            # data = response.json()
            # redirect_url = data.get('redirect_url')
            #
            # if not redirect_url:
            #     messages.error(request, "Réponse invalide de PayCard.")
            #     return  render(request, 'page/donation.html', {'form': form})



            #Send email to donor
            context = {
                'name': str(donor_first_name).capitalize() + ' ' + str(donor_last_name).upper(),
                'amount': amount,
            }
            template_email = 'page/template_email/donation_payment_email.html'
            to_email = [user_email,]
            mail_subject = "Don de financement"
            try:
                print("sending email")
                EmailService.send_template_email(to_email, mail_subject, template_email, context)
                print("email sent")
            except Exception as e:
                print("email not sent", e)
                messages.error(request, "L'envoi du mail a échoué. Veuillez contacter l'administrateur.")
                return  render(request, 'page/donation.html', {'form': form})


            # Redirige vers la page de paiement de PayCard
            # return redirect(redirect_url)
            return redirect('paycard_payment_callback', payment_id=payment.id, type='Don')
        except RequestException as e:
            messages.error(request, "Service PayCard inaccessible. Réessayez plus tard.")
            print("Erreur réseau PayCard:", e)
            return  render(request, 'page/donation.html', {'form': form})

    return render(request, 'page/donation.html', {'form': form})

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
            
            to_email = [email]
            mail_subject = "Message de contact"
            template_email = 'page/template_email/contact_form_email.html'
            try:
                print("sending email")
                EmailService.send_template_email(to_email, mail_subject, template_email, context)

                print("email sent")
            except Exception as e:
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
                    'public_id': str(element.public_id),
                    'progress': element.progress,  # Utilise la propriété progress
                    'days_remaining': element.days_remaining,  # Utilise la propriété days_remaining
                    'amount': element.funding_amount,
                    'details_url': "/funding-request-details/"+str(element.public_id)+"/",          
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
                    'public_id': str(element.public_id),
                    'details_url': "/loss-alert-details/"+str(element.public_id)+"/",  # URL des détails de l'alerte
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

def paycard_funding(request, pk=None, public_id=None):
    if pk is not None:
        funding_request = get_object_or_404(FundingRequest, pk=pk)
        return redirect('paycard_funding_public', public_id=funding_request.public_id, permanent=True)
    else:
        funding_request = get_object_or_404(FundingRequest, public_id=public_id)
    if not funding_request:
        messages.error(request, "Demande de financement non trouvée.")
        return redirect('paycard_funding', pk)
    form = FundingPaymentForm()
    return render(request, 'page/funding_payment.html', {'funding_request': funding_request, 'form': form})


@csrf_protect
def start_paycard_funding_payment(request, funding_id=None, funding_public_id=None):
    if funding_id is not None:
        funding_request = FundingRequest.objects.filter(id=funding_id).first()
    else:
        funding_request = FundingRequest.objects.filter(public_id=funding_public_id).first()

    if not funding_request:
        messages.error(request, "Demande de financement non trouvée.")
        return redirect('paycard_funding', funding_id)
    form = FundingPaymentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            amount = form.cleaned_data['amount']
            user_email = form.cleaned_data['donor_email']
            donor_first_name = form.cleaned_data['donor_first_name']
            donor_last_name = form.cleaned_data['donor_last_name']
            donor_country = form.cleaned_data['donor_country']
            donor_city = form.cleaned_data['donor_city']
            donor_phone = form.cleaned_data['donor_phone']
            donor_address = form.cleaned_data['donor_address']
            try:
                # Enregistrer le paiement dans la base de données
                payment = FundPayment.objects.create(
                    funding_request=funding_request,
                    amount=amount,
                    donor_email=user_email,
                    donor_first_name= donor_first_name,
                    donor_last_name= donor_last_name,
                    donor_address= donor_address,
                    donor_city=donor_city,
                    donor_country=donor_country,
                    donor_phone =donor_phone,
                    transaction_id=str(uuid.uuid4()),  # Générer un ID de transaction unique
                    #reference=data.get('reference')
                )

                # payload = {
                #     "public_key": settings.PAYCARD_API_KEY,
                #     "amount": int(amount),
                #     "currency": "GNF",
                #     "email": user_email,
                #     "description": f"Financement demande #{funding_id}",
                #     "callback_url": request.build_absolute_uri(
                #         reverse('paycard_payment_callback', kwargs={'payment_id': payment.id, 'type': 'Financement'})
                #     )
                #     }
                #
                # response = requests.post(settings.PAYCARD_ENDPOINT, json=payload, timeout=10)
                #
                # if response.status_code != 200:
                #     messages.error(request, "Erreur de communication avec PayCard.")
                #     return  render(request, 'page/funding_payment.html', {'funding_request': funding_request, 'form': form})
                #
                # data = response.json()
                # redirect_url = data.get('redirect_url')
                #
                # if not redirect_url:
                #     messages.error(request, "Réponse invalide de PayCard.")
                #     return  render(request, 'page/funding_payment.html', {'funding_request': funding_request, 'form': form})



                #Send email to donor
                context = {
                    'name': str(donor_first_name).capitalize() + ' ' + str(donor_last_name).upper(),
                    'beneficiary_name': funding_request.beneficiary_name,
                    'amount': amount,
                    'title': funding_request.title,
                }
                template_email = 'page/template_email/funding_payment_email.html'
                to_email = [user_email,]
                mail_subject = "Financement de demande de financement"
                try:
                    print("sending email")
                    EmailService.send_template_email(to_email, mail_subject, template_email, context)
                    print("email sent")
                except Exception as e:
                    print("email not sent", e)
                    messages.error(request, "L'envoi du mail a échoué. Veuillez contacter l'administrateur.")
                    return  render(request, 'page/funding_payment.html', {'funding_request': funding_request, 'form': form})


                # Redirige vers la page de paiement de PayCard
                # return redirect(redirect_url)
                return redirect('paycard_payment_callback', payment_id=funding_id, type='Financement')
            except RequestException as e:
                messages.error(request, "Service PayCard inaccessible. Réessayez plus tard.")
                print("Erreur réseau PayCard:", e)
                return  render(request, 'page/funding_payment.html', {'funding_request': funding_request, 'form': form})

        else:
            return  render(request, 'page/funding_payment.html', {'funding_request': funding_request, 'form': form})

    return redirect('paycard_funding', funding_id)


def paycard_payment_callback(request, payment_id=None, type=None, payment_public_id=None):
    # Logique de validation possible ici (optionnel : appel à PayCard pour vérifier)
    #Update le statut du paiement
    if payment_id is not None:
        payment = FundPayment.objects.filter(id=payment_id).first()
    else:
        payment = FundPayment.objects.filter(public_id=payment_public_id).first()
    if payment:
        payment.status = 'réussi'
        payment.save()
    return render(request,'page/confirmation_page/confirmation_payment.html', {'request':'added', 'type': type})


@login_required
def add_comment(request, model_name, object_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.method == 'POST':
            print("add comment")
            form = CommentForm(request.POST)
            if form.is_valid():
                print("Form valid")
                content_type = ContentType.objects.get(model=model_name.lower())
                comment = form.save(commit=False)
                comment.user = request.user
                comment.content_type = content_type
                comment.object_id = object_id
                comment.save()
                print("Form saved")
                return JsonResponse({
                    'success': True,
                    'comment': {
                        'user': comment.user.username,
                        'text': comment.text,
                        'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
                    }
                })
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Requête invalide'})




def reply_comment(request):
    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('text')
        parent_id = request.POST.get('parent')
        parent = get_object_or_404(Comment, id=parent_id)
        comment = Comment.objects.create(
            user=request.user,
            content_object=parent.content_object,
            parent=parent,
            text=text
        )
        html = render_to_string('page/components/comments/comment_item.html', {'comment': comment, 'user': request.user})
        return JsonResponse({'success': True, 'reply_html': html})
    return JsonResponse({'success': False}, status=400)

def delete_comment(request, pk):
    comment = get_object_or_404(Comment, id=pk, user=request.user)
    comment.delete()
    return JsonResponse({'success': True})


@login_required
@require_POST
def edit_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
    except Comment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Commentaire non trouvé'}, status=404)

    new_text = request.POST.get('text', '').strip()
    if new_text:
        comment.text = new_text
        comment.save()
        return JsonResponse({'success': True, 'text': comment.text})
    return JsonResponse({'success': False, 'error': 'Texte invalide'}, status=400)


@login_required
@require_POST
def delete_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
        comment.delete()
        return JsonResponse({'success': True})
    except Comment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Commentaire introuvable'}, status=404)


@login_required
@require_POST
def report_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id)
        # Optionnel : logguer ou sauvegarder dans une table Report si nécessaire
        print(f"Commentaire signalé par {request.user.username}: {comment.text}")
        return JsonResponse({'success': True, 'message': 'Le commentaire a été signalé'})
    except Comment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Commentaire introuvable'}, status=404)




