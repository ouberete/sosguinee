from base64 import urlsafe_b64decode
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.utils.encoding import force_str
from smtplib import SMTPException
from page.models import UserDetails
from sosguinee import settings
from .forms import LoginForm, ProfileForm, RegisterForm, UserDocumentForm, UserInfosForm, UserLinkForm
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.views.generic.edit import FormView
#from formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage



# Create your views here.
def signin(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request.POST or None)
    if form.is_valid():
        # form.cleaned_data['user'] est déjà l’instance User validée.
        user = form.cleaned_data['user']

        # On appelle bien auth_login pour créer la session
        auth_login(request, user)
        return redirect('home')

    return render(request, 'accounts/login.html', {'form': form})
   

def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        # on set request sur le form pour send_mail
        form.request = request  
        if form.is_valid():
            form.save()
            return render(request, 'accounts/account_created.html', {
                'email': form.cleaned_data['email']
            })
    else:
        form = RegisterForm()

    return render(request, 'accounts/signup.html', {
        'form': form
    })



def reset(request):
    return render(request, 'accounts/reset-password.html')

""" def user_profile(request):
    
    print(request.user)
    if request.user.is_authenticated:
        print("user authenticated")
        # Récupérer l'objet UserDetails associé à l'utilisateur connecté
        try:
            profile = UserDetails.objects.get(user=request.user)
         
            user_details = ProfileForm(instance=profile)
            
            countries = dict(UserDetails.COUNTRY_CHOICES)
            country = countries.get(profile.birth_country, 'Non renseigne')
            
            nationality =  countries.get(profile.nationality, 'Non renseigne')
            
            civilities = dict(UserDetails.CIVILITY_CHOICES)
            civility = civilities.get(profile.civility, 'Non renseigne')
            
            professions = dict(UserDetails.PROFESSION_CHOICES)
            profession = professions.get(profile.profession, 'Non renseigne')
            
            categories = dict(UserDetails.USER_CATEGORY_CHOICES)
            category = categories.get(profile.user_category, 'Non renseigne')
           
            return render(request, 'accounts/profil.html', {'profile': profile, 'country': country, 'civility': civility, 'profession': profession,
                'nationality': nationality, 'category': category})
        except UserDetails.DoesNotExist:
            # Gérer le cas où UserDetails n'existe pas pour cet utilisateur
            return redirect('login')
    else:
        # Gérer le cas où l'utilisateur n'est pas connecté
        return redirect('accueil')
   """ 
def activate(request, uidb64, token):
    try:
        
       # uid = int(urlsafe_base64_decode(uidb64).decode())
        user = User.objects.get(pk=uidb64)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):     
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        # Activation réussie, activer le compte de l'utilisateur
        # Check if user account is activated
        if user.is_active:
            return render(request, 'accounts/account_activated.html', {'error': "Votre compte est déjà activé."})
        user.is_active = True
        user.save()
        return render(request, 'accounts/account_activated.html', {'success':  "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter."})
    else:
        # Lien d'activation invalide
        return render(request, 'accounts/account_activated.html', {'error': "Le lien d'activation est invalide ou a expiré."})
            
     
def user_logout(request):
    logout(request)
    return redirect('home')
    

def acount_created(request):
    return render(request, 'accounts/account_created.html')


""" class UserInfosView(FormView):
    template_name = 'accounts/user_infos.html'
    form_class = UserInfosForm
    success_url = 'user-document'

    def form_valid(self, form):
        # Traitement de la première étape
        return super().form_valid(form)

class UserDocumentView(FormView):
    template_name = 'accounts/user_document.html'
    form_class = UserDocumentForm
    success_url = 'user-link'

    def form_valid(self, form):
        # Traitement de la deuxième étape
        return super().form_valid(form)

class UserLinkView(FormView):
    template_name = 'accounts/user_link.html'
    form_class = UserLinkForm
    success_url = 'update_profile'

    def form_valid(self, form):
        # Traitement de la troisième étape
        return super().form_valid(form)

class UpdateUserProfileWizard(SessionWizardView):
    # Définissez les formulaires et les étapes
    template_name = 'accounts/update_profile.html'  # Template global pour le wizard
    file_storage = FileSystemStorage(location='/tmp')
    # Étapes du wizard
    
    
    
    def get_form(self, step=None, **kwargs):
        
        if self.request.user.is_authenticated:
            print("user authenticated")
            # Récupérer l'objet UserDetails associé à l'utilisateur connecté
            try:
                profile = UserDetails.objects.get(user=self.request.user)
                print("got profile", profile)
                user_details = ProfileForm(instance=profile)
                # Utiliser user_details dans votre logique de vue
                #return render(request, 'accounts/profil.html', {'profile': profile})
                print("got infos 1", self.request.POST)
                if step == 'user-infos':
                    print("got infos", self.request.POST)
                    return UserInfosForm(data=profile or None, **kwargs)
                elif step == 'user-document':
                    return UserDocumentForm(data=self.request.POST or None, **kwargs)
                elif step == 'user-link':
                    return UserLinkForm(data=self.request.POST or None, **kwargs)
                return super().get_form(step, **kwargs)
            
            except UserDetails.DoesNotExist:
                # Gérer le cas où UserDetails n'existe pas pour cet utilisateur
                return redirect('login')
        else:
            # Gérer le cas où l'utilisateur n'est pas connecté
            return redirect('accueil')
       

    # Fonction de validation de chaque étape
    def done(self, form_list, **kwargs):
       # Récupérer les données soumises dans chaque étape du formulaire
        data = {k: v for form in form_list for k, v in form.cleaned_data.items()}
        userDetails =  UserDetails()
        userDetails.first_name = data['first_name']
        userDetails.last_name = data['last_name']
        userDetails.birth_date = data['birth_date']
        userDetails.birth_city = data['birth_city']
        userDetails.nationality = data['nationality']
        userDetails.is_actual_country_as_birth_country = data['is_actual_country_as_birth_country']
        userDetails.actual_city = data['actual_city']
        userDetails.actual_country = data['actual_country']
        userDetails.zip_code = data['zip_code']
        userDetails.address = data['address']
        userDetails.phone = data['phone']
        userDetails.profession_situation = data['profession_situation']
        userDetails.activity_sector = data['activity_sector']
        userDetails.profession = data['profession']
        userDetails.high_education = data['high_education']
        userDetails.person_contact = data['person_contact']
        userDetails.user_category = data['user_category']
        userDetails.civility = data['civility']
        userDetails.bio = data['bio']
        userDetails.photo = data['photo']
        userDetails.id_card = data['id_card']
        userDetails.id_card_country = data['id_card_country']
        userDetails.birth_piece = data['birth_piece']
        userDetails.birth_piece_country = data['birth_piece_country']
        userDetails.facebook = data['facebook']
        userDetails.twitter = data['twitter']
        userDetails.linkedin = data['linkedin']
        userDetails.instagram = data['instagram']
        userDetails.save()
        
        # Vous pouvez accéder aux données de chaque formulaire via form_list
        # Effectuez ici le traitement final ou la sauvegarde des données
        return HttpResponseRedirect('/profile/')
    
    

 """
 
class UserInfosView(FormView):
    template_name = 'accounts/user_infos.html'
    form_class = UserInfosForm
    success_url = 'user-document'

    def form_valid(self, form):
        # Traitement de la première étape
        return super().form_valid(form)
    
    

class UserDocumentView(FormView):
    template_name = 'accounts/user_document.html'
    form_class = UserDocumentForm
    success_url = 'user-link'

    def form_valid(self, form):
        # Traitement de la deuxième étape
        return super().form_valid(form)

class UserLinkView(FormView):
    template_name = 'accounts/user_link.html'
    form_class = UserLinkForm
    success_url = 'update_profile'

    def form_valid(self, form):
        # Traitement de la troisième étape
        return super().form_valid(form)


"""
class UpdateUserProfileWizard(SessionWizardView):
    template_name = 'accounts/update_profile.html'  # Template global pour le wizard
    file_storage = FileSystemStorage(location='/tmp')
    form_list = [("user-infos", UserInfosForm),
                 ("user-document", UserDocumentForm),
                 ("user-link", UserLinkForm)]

    def get_form_instance(self, step):
        if self.request.user.is_authenticated:
            try:
                profile = UserDetails.objects.get(user=self.request.user)
                return profile
            except UserDetails.DoesNotExist:
                return None
        return None

    def get_form_kwargs(self, step):
        if self.request.user.is_authenticated:
            profile = self.get_form_instance(step)
            if profile:
                if step == 'user-infos':
                    return {'instance': profile}
                elif step == 'user-document':
                    return {'instance': profile}
                elif step == 'user-link':
                    return {'instance': profile}
        return {}

#models.FileField(upload_to='user_images/id_cards', blank=True, null=True)

    def get_form(self, step=None, data=None, files=None):
        form = super().get_form(step, data=data, files=files)
        if step == 'user-document':
            form.fields['id_card'].widget.attrs.update({'class': 'form-control'})
            form.fields['photo'].widget.attrs.update({'class': 'form-control'})
            form.fields['birth_piece'].widget.attrs.update({'class': 'form-control'})
        return form

    def done(self, form_list, **kwargs):
        data = {}
        files = {}
        for form in form_list:
            data.update(form.cleaned_data)
            for field_name, field_value in form.cleaned_data.items():
                if field_value and hasattr(field_value, 'file'):
                    files[field_name] = field_value

        user_details, created = UserDetails.objects.update_or_create(
            user=self.request.user,
            defaults=data
        )
        
        # Traitement des fichiers
        for field_name, field_value in files.items():
            if field_value:
                setattr(user_details, field_name, field_value)
        user_details.is_completed = True
        user_details.save()
        
        return HttpResponseRedirect('/profile')
 
 def update_profile(request):
    
    if request.user.is_authenticated:
        print("user authenticated")
        # Récupérer l'objet UserDetails associé à l'utilisateur connecté
        try:
            profile = UserDetails.objects.get(user=request.user)
            print("got profile", profile)
            user_details = UserInfosForm(instance=profile)
            # Utiliser user_details dans votre logique de vue
            return render(request, 'accounts/update_profile.html', {'profile': user_details})
        except UserDetails.DoesNotExist:
            # Gérer le cas où UserDetails n'existe pas pour cet utilisateur
            return redirect('login')
    else:
        # Gérer le cas où l'utilisateur n'est pas connecté
        return redirect('accueil')
    
  """   

"""
def logout(request):
    return render(request, 'accounts/logout.html')

def password_reset(request):
    return render(request, 'accounts/password_reset.html')

def password_reset_done(request):
    return render(request, 'accounts/password_reset_done.html')

def password_reset_confirm(request):
    return render(request, 'accounts/password_reset_confirm.html')

def password_reset_complete(request):
    return render(request, 'accounts/password_reset_complete.html')

def password_change(request):
    return render(request, 'accounts/password_change.html')

def password_change_done(request):
    return render(request, 'accounts/password_change_done.html')

def email_change(request):
    return render(request, 'accounts/email_change.html')

def email_change_done(request):
    return render(request, 'accounts/email_change_done.html')

def email_change_confirm(request):
    return render(request, 'accounts/email_change_confirm.html')

def email_change_confirm_done(request):
    return render(request, 'accounts/email_change_confirm_done.html')
    
"""

def otp_login_view(request):
    return render(request, 'accounts/otp_login.html')