<<<<<<< HEAD
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
=======
import hashlib
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from sosguinee.utils.captcha import get_turnstile_site_key, verify_turnstile_request
from sosguinee.utils.utilities import Utilities

from accounts.utils import send_or_queue_activation_email
from page.models import UserDetails
from ..forms import LoginForm, RegisterForm, ResendActivationForm


AUTH_RATE_LIMIT_MESSAGE = "Trop de tentatives. Veuillez réessayer dans quelques minutes."
logger = logging.getLogger(__name__)


def _site_protocol_domain():
    site_url = (getattr(settings, "SITE_URL", "") or "http://localhost:8000").rstrip("/")
    parsed = urlparse(site_url)
    protocol = parsed.scheme or ("https" if not settings.DEBUG else "http")
    domain = parsed.netloc or parsed.path
    return protocol, domain


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _rate_limit_key(scope, request, identifier=""):
    raw_key = f"{scope}:{_client_ip(request)}:{identifier}".lower().encode("utf-8")
    return "auth-rate-limit:" + hashlib.sha256(raw_key).hexdigest()


def _is_rate_limited(scope, request, identifier="", limit=5, window=900):
    key = _rate_limit_key(scope, request, identifier)
    attempts = cache.get(key, 0)
    if attempts >= limit:
        return True

    if attempts == 0:
        cache.add(key, 1, window)
    else:
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, attempts + 1, window)
    return False


def signin(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = LoginForm(request.POST or None)
    if request.method == "POST":
        identifier = (request.POST.get("username") or "").strip()
        if _is_rate_limited("login", request, identifier=identifier, limit=6, window=900):
            form.add_error(None, AUTH_RATE_LIMIT_MESSAGE)
        else:
            captcha_ok, captcha_error = verify_turnstile_request(request)
            if not captcha_ok:
                form.add_error(None, captcha_error)
            elif form.is_valid():
                cache.delete(_rate_limit_key("login", request, identifier))
                auth_login(request, form.cleaned_data["user"])
                return redirect("home")

    return render(request, "accounts/login.html", {
        "form": form,
        "turnstile_site_key": get_turnstile_site_key(),
    })


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        form.request = request
        email = (request.POST.get("email") or "").strip()
        if _is_rate_limited("register", request, identifier=email, limit=4, window=3600):
            form.add_error(None, AUTH_RATE_LIMIT_MESSAGE)
        else:
            captcha_ok, captcha_error = verify_turnstile_request(request)
            if not captcha_ok:
                form.add_error(None, captcha_error)
            elif form.is_valid():
                form.save()
                cache.delete(_rate_limit_key("register", request, email))
                return render(request, "accounts/account_created.html", {
                    "email": form.cleaned_data["email"],
                })
    else:
        form = RegisterForm()

    return render(request, "accounts/signup.html", {
        "form": form,
        "turnstile_site_key": get_turnstile_site_key(),
    })


def resend_activation(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = ResendActivationForm(request.POST)
        identifier = (request.POST.get("identifier") or "").strip()
        if _is_rate_limited("resend-activation", request, identifier=identifier, limit=4, window=3600):
            form.add_error(None, AUTH_RATE_LIMIT_MESSAGE)
        elif form.is_valid():
            user = (
                User.objects
                .filter(Q(username__iexact=identifier) | Q(email__iexact=identifier))
                .first()
            )
            if user and not user.is_active:
                profile = UserDetails.objects.filter(user=user).order_by("-created_at").first()
                if profile and profile.user_status == "Blocked":
                    messages.success(
                        request,
                        "Si un compte inactif existe, un lien d'activation a ete envoye.",
                    )
                    cache.delete(_rate_limit_key("resend-activation", request, identifier))
                    return redirect("login")
                try:
                    send_or_queue_activation_email(user, reuse_unsent=True)
                except Exception as e:
                    logger.exception("Renvoi du lien d'activation non envoye: %s", e)

            messages.success(
                request,
                "Si un compte inactif existe, un lien d'activation a ete envoye.",
            )
            cache.delete(_rate_limit_key("resend-activation", request, identifier))
            return redirect("login")
    else:
        form = ResendActivationForm()

    return render(request, "accounts/resend_activation.html", {"form": form})


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        profile = UserDetails.objects.filter(user=user).order_by("-created_at").first()
        if profile and profile.user_status == "Blocked":
            return render(request, "accounts/account_activated.html", {
                "error": "Ce compte a ete bloque. Veuillez contacter l'administrateur.",
            })
        if user.is_active:
            return render(request, "accounts/account_activated.html", {
                "error": "Votre compte est déjà activé.",
            })
        user.is_active = True
        user.save(update_fields=["is_active"])
        profile, _ = UserDetails.objects.get_or_create(user=user, defaults={"user_status": "Active"})
        if profile.user_status != "Blocked":
            profile.user_status = "Active"
            profile.save(update_fields=["user_status"])
        return render(request, "accounts/account_activated.html", {
            "success": "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.",
        })

    return render(request, "accounts/account_activated.html", {
        "error": "Le lien d'activation est invalide ou a expiré.",
    })


def user_logout(request):
    logout(request)
    return redirect("home")


def acount_created(request):
    return render(request, "accounts/account_created.html")


def reset_password(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        email = (request.POST.get("email") or "").strip()
        if _is_rate_limited("password-reset", request, identifier=email, limit=4, window=3600):
            form.add_error(None, AUTH_RATE_LIMIT_MESSAGE)
        elif form.is_valid():
            protocol, domain = _site_protocol_domain()
            users = list(form.get_users(form.cleaned_data.get("email")))

            for user in users:
                context = {
                    "user": user,
                    "domain": domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "protocol": protocol,
                    "token": default_token_generator.make_token(user),
                }
                try:
                    Utilities.sending_email(
                        "accounts/emails/password_reset_email.html",
                        [user.email],
                        context,
                        "Réinitialisation de votre mot de passe",
                    )
                except Exception:
                    if settings.DEBUG:
                        raise
            messages.success(
                request,
                "Si un compte existe pour cet email, un lien de réinitialisation a été envoyé.",
            )
            cache.delete(_rate_limit_key("password-reset", request, email))
            return redirect("password_reset_done")
    else:
        form = PasswordResetForm()

    return render(request, "accounts/reset_password.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
>>>>>>> chore/security-design-hardening
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Votre mot de passe a été modifié avec succès.")
<<<<<<< HEAD
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {"form": form})

def otp_login_view(request):
    return render(request, 'accounts/otp_login.html')
=======
            return redirect("profile")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/change_password.html", {"form": form})


def otp_login_view(request):
    return render(request, "accounts/otp_login.html")
>>>>>>> chore/security-design-hardening
