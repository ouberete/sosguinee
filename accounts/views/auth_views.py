from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils.encoding import force_str
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from ..forms import LoginForm, RegisterForm
from django.conf import settings
from sosguinee.utils.utilities import Utilities

def signin(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request.POST or None)
    if form.is_valid():
        # form.cleaned_data['user'] est déjà l'instance User validée.
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

def activate(request, uidb64, token):
    try:
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

def reset_password(request):
    # Simple reset via Django PasswordResetForm
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            users = list(form.get_users(email))

            # Domain/protocol comme pour l'activation
            if settings.DEBUG:
                domain = "127.0.0.1:7400"
                protocol = "http"
            else:
                domain = "18.170.114.4"
                protocol = "http"

            for user in users:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                context = {
                    'user': user,
                    'domain': domain,
                    'uid': uid,
                    'protocol': protocol,
                    'token': token,
                }
                subject = "Réinitialisation de votre mot de passe"
                try:
                    Utilities.sending_email("accounts/emails/password_reset_email.html", [user.email], context, subject)
                except Exception:
                    if not settings.DEBUG:
                        # en prod, on reste silencieux pour éviter de divulguer l'existence des emails
                        pass
                    else:
                        raise
            messages.success(request, "Si un compte existe pour cet email, un lien de réinitialisation a été envoyé.")
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request, 'accounts/reset_password.html', {"form": form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Votre mot de passe a été modifié avec succès.")
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {"form": form})

def otp_login_view(request):
    return render(request, 'accounts/otp_login.html')
