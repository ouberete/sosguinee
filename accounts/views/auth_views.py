from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.utils.encoding import force_str
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator

from ..forms import LoginForm, RegisterForm

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
    return render(request, 'accounts/reset-password.html')

def change_password(request):
    return render(request, 'accounts/password_change.html')

def otp_login_view(request):
    return render(request, 'accounts/otp_login.html')