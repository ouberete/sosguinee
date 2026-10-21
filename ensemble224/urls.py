"""
URL configuration for ensemble224 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/

s:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.urls import include, path, re_path, reverse_lazy
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.static import serve

from accounts.views.documents import protected_user_document
from page import views as page_views



def healthz(request):

    """Sonde de vivacité pour Kubernetes/monitoring: pas d'accès base."""
    return JsonResponse({"status": "ok"})


def readyz(request):
    """Sonde de disponibilité: vérifie la base et le cache partagés."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        cache.get("__readiness_probe__")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def robots_txt(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    content = "\n".join(
        [
            "User-agent: *",
            "Disallow: /admin/",
            "Disallow: /accounts/",
            "Allow: /",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    static_paths = [
        reverse_lazy("home"),
        reverse_lazy("loss_alert_list"),
        reverse_lazy("funding_request_list"),
        reverse_lazy("add_loss_alert"),
        reverse_lazy("add_funding_request"),
        reverse_lazy("donation"),
        reverse_lazy("about_us"),
        reverse_lazy("contact"),
        reverse_lazy("help_support"),
        reverse_lazy("policy_privacy"),
        reverse_lazy("terms"),
    ]
    urls = "\n".join(
        f"  <url><loc>{request.build_absolute_uri(path)}</loc></url>"
        for path in static_paths
    )
    content = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n'
    return HttpResponse(content, content_type="application/xml")


@xframe_options_sameorigin
def public_media(request, path):
    """Serve public attachments with same-origin framing enabled for previews."""
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    # Pour le changement de langue (set_language)
    path("i18n/", include("django.conf.urls.i18n")),
    # Webhook externe: hors i18n pour garder une URL stable côté PSP.
    path("djomy/webhook/", page_views.djomy_webhook, name="djomy_webhook"),
    # Sonde de santé (probes Kubernetes, load balancer)
    path("healthz/", healthz, name="healthz"),
    path("readyz/", readyz, name="readyz"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),
    # Documents personnels (pièces d'identité...): accès contrôlé par Django.
    # Déclaré AVANT les patterns statiques pour les intercepter;
    # en production, nginx/l'ingress route ce préfixe vers Django.
    path("media/user_images/<path:path>", protected_user_document, name="protected_user_document"),
    # Endpoints API hors i18n (évite les redirections 302 pour fetch / ajax)
    path("api/", include("page.api_urls")),
]


urlpatterns  += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('page.urls')),
    path('', include('accounts.urls')),
    # Only password reset flow from Django auth (exclude login/logout)
    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('login')), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/', include('allauth.urls')),
    path('', include('django_djomy.urls')),
)

# Route média : sert les images publiques (img/Fundings, img/Alerts, etc.)
# Ne court-circuite pas /media/user_images/ qui est déclaré plus haut dans urlpatterns.
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", public_media),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)



handler404 = "page.views.custom_404"
