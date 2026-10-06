from django.conf import settings


def analytics(request):
    return {
        "plausible_domain": getattr(settings, "PLAUSIBLE_DOMAIN", ""),
    }
