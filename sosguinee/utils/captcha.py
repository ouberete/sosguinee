import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_turnstile_site_key():
    return (getattr(settings, "TURNSTILE_SITE_KEY", "") or "").strip()


def is_turnstile_enabled():
    site_key = get_turnstile_site_key()
    secret_key = (getattr(settings, "TURNSTILE_SECRET_KEY", "") or "").strip()
    return bool(site_key and secret_key)


def verify_turnstile_request(request):
    """
    Vérifie le captcha Turnstile envoyé par le formulaire.
    Retourne (is_valid, error_message).
    """
    if not is_turnstile_enabled():
        if settings.DEBUG:
            return True, ""
        return False, "Configuration CAPTCHA manquante. Veuillez contacter l'administrateur."

    token = (request.POST.get("cf-turnstile-response") or "").strip()
    if not token:
        return False, "Veuillez valider le CAPTCHA."

    verify_url = (
        getattr(settings, "TURNSTILE_VERIFY_URL", "")
        or "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    )
    payload = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
        "remoteip": request.META.get("REMOTE_ADDR", ""),
    }
    try:
        response = requests.post(verify_url, data=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
    except Exception as exc:
        logger.warning("Erreur vérification CAPTCHA Turnstile: %s", exc)
        return False, "Vérification CAPTCHA indisponible. Réessayez dans un instant."

    if result.get("success"):
        return True, ""

    logger.warning("CAPTCHA Turnstile invalide: %s", result.get("error-codes"))
    return False, "Échec de validation CAPTCHA. Veuillez réessayer."
