import uuid
import json
import hmac
import hashlib
import logging
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from smtplib import SMTPException
from urllib.parse import urljoin, urlparse, urlunparse

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_GET, require_POST
from django.utils.crypto import constant_time_compare

from page.models import FundingRequest, LossAlert, FundingType, LossAlertType, LossAlertStatus, FundingRequestStatus, \
    Donation, FundPayment, Comment, UserActionLog, Report
from page.forms import DonationForm, FundingRequestForm, LossAlertForm, MessageContactForm, FundingPaymentForm, \
    CommentForm
from page.services.loss_alert_service import LossAlertService
from page.services.funding_request_service import FundingRequestService
from django.core.paginator import Paginator
from page.models import UserDetails
from sosguinee.utils.email_service import EmailService
<<<<<<< HEAD
from django.views.decorators.csrf import csrf_protect
=======
from django.views.decorators.csrf import csrf_protect, csrf_exempt
>>>>>>> chore/security-design-hardening
from django.conf import settings
from django.contrib import messages
import requests
from requests.exceptions import RequestException
from django.http import HttpResponseForbidden
<<<<<<< HEAD
=======
from sosguinee.utils.captcha import get_turnstile_site_key, verify_turnstile_request
>>>>>>> chore/security-design-hardening
User = get_user_model()
logger = logging.getLogger(__name__)
ALLOWED_COMMENT_MODELS = {
    "fundingrequest": FundingRequest,
    "lossalert": LossAlert,
}
PUBLIC_RATE_LIMIT_MESSAGE = "Trop de tentatives. Veuillez reessayer dans quelques minutes."


def _is_valid_payment_callback_token(payment, token):
    if not payment or not token:
        return False
    tx = (payment.transaction_id or "").strip()
    return bool(tx) and constant_time_compare(token, tx)


def _captcha_context():
    return {"turnstile_site_key": get_turnstile_site_key()}


def _normalize_label(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _find_status_by_keywords(queryset, keywords):
    normalized_keywords = tuple(_normalize_label(k) for k in keywords if k)
    for status in queryset:
        normalized_name = _normalize_label(getattr(status, "name", ""))
        if any(keyword in normalized_name for keyword in normalized_keywords):
            return status
    return None


def _resolve_or_create_status(model, fallback_name, fallback_description, keywords):
    status = _find_status_by_keywords(model.objects.all(), keywords)
    if status:
        return status

    status = model.all_objects.filter(name__iexact=fallback_name).first()
    if status:
        if getattr(status, "isDeleted", False):
            status.isDeleted = False
            status.description = status.description or fallback_description
            status.save(update_fields=["isDeleted", "description", "updated_at"])
        return status

    return model.objects.create(name=fallback_name, description=fallback_description)


def _prefill_donor_initial_data(request):
    if not request.user.is_authenticated:
        return {}

    profile = UserDetails.objects.filter(user=request.user).order_by("-created_at").first()

    first_name = (getattr(request.user, "first_name", "") or "").strip()
    last_name = (getattr(request.user, "last_name", "") or "").strip()
    email = (getattr(request.user, "email", "") or "").strip()
    phone = ""
    address = ""
    city = ""
    country = ""

    if profile:
        first_name = first_name or (profile.first_name or "").strip()
        last_name = last_name or (profile.last_name or "").strip()
        email = email or (profile.email or "").strip()
        phone = (profile.phone or "").strip()
        address = (profile.address or "").strip()
        city = (profile.actual_city or profile.birth_city or profile.location or "").strip()
        country = (
            (profile.actual_country or "").strip()
            or (profile.nationality or "").strip()
            or (profile.birth_country or "").strip()
        )

    return {
        "donor_first_name": first_name,
        "donor_last_name": last_name,
        "donor_email": email,
        "donor_phone": phone,
        "donor_address": address,
        "donor_city": city,
        "donor_country": country,
    }


def _client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _rate_limit_key(scope, request, identifier=""):
    raw_key = f"{scope}:{_client_ip(request)}:{identifier}".lower().encode("utf-8")
    return "page-rate-limit:" + hashlib.sha256(raw_key).hexdigest()


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


def _get_payment_success_status(payment):
    choices = list(payment._meta.get_field("status").choices or [])
    if len(choices) >= 2:
        return choices[1][0]
    return payment.status


def _finalize_funding_request_status(funding_request):
    if not funding_request:
        return False
    if (funding_request.amount_received or 0) < funding_request.funding_amount:
        return False
    done_status = _resolve_or_create_status(
        FundingRequestStatus,
        fallback_name="Terminé",
        fallback_description="Statut de fin de collecte.",
        keywords=("termine", "clos", "cloture"),
    )
    if not done_status or funding_request.funding_request_status_id == done_status.id:
        return False
    funding_request.funding_request_status = done_status
    funding_request.save(update_fields=["funding_request_status", "updated_at"])
    return True


def _send_payment_success_email(payment):
    try:
        if isinstance(payment, Donation):
            EmailService.send_donation_notification(payment)
            return True
        if isinstance(payment, FundPayment):
            context = {
                'name': str(payment.donor_first_name or '').capitalize() + ' ' + str(payment.donor_last_name or '').upper(),
                'beneficiary_name': payment.funding_request.beneficiary_name if payment.funding_request else '',
                'amount': payment.amount,
                'title': payment.funding_request.title if payment.funding_request else '',
            }
            template_email = 'page/template_email/funding_payment_email.html'
            to_email = [payment.donor_email] if payment.donor_email else []
            if to_email:
                EmailService.send_template_email(to_email, "Financement de demande de financement", template_email, context)
                return True
    except Exception as exc:
        logger.warning("Email de confirmation de paiement non envoyé: %s", exc, exc_info=True)
    return False


def _log_payment_event(event, **kwargs):
    payload = {"event": event, **kwargs}
    logger.info("payment_event=%s", json.dumps(payload, ensure_ascii=False, default=str))


def _force_https(url):
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return url
    return urlunparse(parsed._replace(scheme="https"))


def _build_public_absolute_uri(request, relative_path):
    site_url = (getattr(settings, "SITE_URL", "") or "").strip()
    if site_url:
        base = site_url if site_url.endswith("/") else f"{site_url}/"
        return _force_https(urljoin(base, relative_path.lstrip("/")))
    return _force_https(request.build_absolute_uri(relative_path))


def _extract_signature_candidates(signature_header):
    if not signature_header:
        return []
    raw = signature_header.strip()
    candidates = {raw}
    for part in raw.split(','):
        token = part.strip()
        if not token:
            continue
        candidates.add(token)
        if '=' in token:
            _, value = token.split('=', 1)
            if value:
                candidates.add(value.strip())
    return [c for c in candidates if c]


def _verify_djomy_webhook_signature(request):
    secret = (getattr(settings, "DJOMY_WEBHOOK_SECRET", "") or "").strip()
    if not secret:
        if settings.DEBUG:
            logger.warning("DJOMY_WEBHOOK_SECRET absent: signature webhook non vÃ©rifiÃ©e (mode DEBUG).")
            return True
        return False

    signature_header = (
        request.headers.get("X-Djomy-Signature")
        or request.headers.get("Djomy-Signature")
        or request.headers.get("X-Webhook-Signature")
        or request.headers.get("X-Signature")
    )
    if not signature_header:
        return False

    timestamp = (
        request.headers.get("X-Djomy-Timestamp")
        or request.headers.get("Djomy-Timestamp")
        or request.headers.get("X-Webhook-Timestamp")
    )
    raw_body = request.body or b""

    expected_signatures = set()
    digest_body = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    expected_signatures.update({digest_body, f"sha256={digest_body}", f"v1={digest_body}"})
    if timestamp:
        signed_payload = f"{timestamp}.{raw_body.decode('utf-8', errors='ignore')}".encode("utf-8")
        digest_ts = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        expected_signatures.update({digest_ts, f"sha256={digest_ts}", f"v1={digest_ts}"})

    candidates = _extract_signature_candidates(signature_header)
    for candidate in candidates:
        lowered_candidate = candidate.lower()
        for expected in expected_signatures:
            if constant_time_compare(lowered_candidate, expected.lower()):
                return True
    return False


def _get_payload_sources(payload):
    sources = []
    if isinstance(payload, dict):
        sources.append(payload)
        for key in ("data", "payment", "transaction", "payload", "event"):
            value = payload.get(key)
            if isinstance(value, dict):
                sources.append(value)
    return sources


def _extract_first_non_empty(payload, keys):
    for source in _get_payload_sources(payload):
        for key in keys:
            value = source.get(key)
            if value not in (None, ""):
                return value
    return None


def _normalize_payment_status(raw_status):
    if raw_status is None:
        return None
    status = str(raw_status).strip().lower()
    if status in {"success", "succeeded", "paid", "completed", "complete", "rÃ©ussi", "reussi"}:
        return "rÃ©ussi"
    if status in {"failed", "failure", "error", "cancelled", "canceled", "declined", "Ã©chouÃ©", "echoue"}:
        return "Ã©chouÃ©"
    if status in {"pending", "en_attente", "processing"}:
        return "en_attente"
    return status


def _extract_djomy_redirect_url(response_data):
    """
    Extrait l'URL de redirection de la rÃ©ponse Djomy en supportant
    plusieurs formats de payload.
    """
    if not isinstance(response_data, dict):
        return None

    # Format direct
    for key in ("paymentUrl", "redirectUrl", "url"):
        value = response_data.get(key)
        if value:
            return value

    # Format encapsulÃ© sous "data"
    data = response_data.get("data")
    if isinstance(data, dict):
        for key in ("paymentUrl", "redirectUrl", "url"):
            value = data.get(key)
            if value:
                return value

    return None


def _resolve_webhook_payment(payload):
    reference = _extract_first_non_empty(
        payload,
        (
            "reference",
            "ref",
            "merchant_reference",
            "merchantPaymentReference",
            "payment_reference",
            "external_reference",
            "order_ref",
        ),
    )
    tx_id = _extract_first_non_empty(
        payload,
        ("transaction_id", "transactionId", "txid", "payment_id", "paymentId"),
    )

    reference_str = str(reference).strip() if reference is not None else ""
    tx_str = str(tx_id).strip() if tx_id is not None else ""
    ref_upper = reference_str.upper()

    model = None
    payment = None
    if ref_upper.startswith("DON_"):
        model = Donation
        payment = Donation.objects.filter(transaction_id=reference_str[4:]).first()
    elif ref_upper.startswith("FUND_"):
        model = FundPayment
        payment = FundPayment.objects.filter(transaction_id=reference_str[5:]).first()

    if payment is None and reference_str:
        payment = FundPayment.objects.filter(reference=reference_str).first()
        model = FundPayment if payment else model
    if payment is None and reference_str:
        payment = Donation.objects.filter(reference=reference_str).first()
        model = Donation if payment else model

    if payment is None and tx_str:
        payment = FundPayment.objects.filter(transaction_id=tx_str).first()
        model = FundPayment if payment else model
    if payment is None and tx_str:
        payment = Donation.objects.filter(transaction_id=tx_str).first()
        model = Donation if payment else model

    return model, payment, reference_str, tx_str
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
    funding_request_statuses = FundingRequestStatus.objects.all().exclude(name="Clos").exclude(name="TrouvÃ©")
                
    return render(request, 'page/funding_requests.html', {'funding_request_types': funding_request_types, 'funding_request_statuses': funding_request_statuses})

def loss_alert_list(request):
    loss_alert_types = LossAlertType.objects.all()
    loss_alert_statuses = LossAlertStatus.objects.all().exclude(name="Clos").exclude(name="TrouvÃ©")
    return render(request, 'page/loss_alerts.html', {'loss_alert_types': loss_alert_types, 'loss_alert_statuses': loss_alert_statuses})

def add_funding_request(request):
    if request.method == 'POST':
        form = FundingRequestForm(request.POST, request.FILES)
<<<<<<< HEAD
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
                'region': str(fundingRequest.region) if fundingRequest.region else '',
                'prefecture': str(fundingRequest.prefecture) if fundingRequest.prefecture else '',
                'commune': str(fundingRequest.commune) if fundingRequest.commune else '',
                'quarter': str(fundingRequest.quarter) if fundingRequest.quarter else '',
                'address': fundingRequest.address,
                'amount': fundingRequest.funding_amount,
                'email': fundingRequest.email,
                'phone': fundingRequest.phone,
                'commune': str(fundingRequest.commune) if fundingRequest.commune else '',
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
=======
        identifier = (request.POST.get("email") or request.POST.get("phone") or "").strip()
        if _is_rate_limited("add-funding-request", request, identifier=identifier, limit=3, window=3600):
            form.add_error(None, PUBLIC_RATE_LIMIT_MESSAGE)
            context = {'form': form}
            context.update(_captcha_context())
            return render(request, 'page/add_funding_request.html', context)
        captcha_ok, captcha_error = verify_turnstile_request(request)
        if not captcha_ok:
            form.add_error(None, captcha_error)
        elif form.is_valid():
            fundingRequest = FundingRequestService.create_funding_request_from_form(request, form, identifier)
            
            if identifier:
                cache.delete(_rate_limit_key("add-funding-request", request, identifier))
>>>>>>> chore/security-design-hardening
            
            return render(request,'page/confirmation_page/confirmation_funding_request_added.html', {'request':'added'})
        else:
            errors = form.errors
            context = {'form': form, 'errors': errors}
            context.update(_captcha_context())
            return render(request, 'page/add_funding_request.html', context)
    else:
        form = FundingRequestForm()
    context = {'form': form}
    context.update(_captcha_context())
    return render(request, 'page/add_funding_request.html', context)


@login_required
def edit_funding_request(request, public_id):
    fr = FundingRequest.objects.filter(public_id=public_id).first()
    if not fr or fr.created_by != request.user:
        return HttpResponseForbidden("Vous n'Ãªtes pas autorisÃ© Ã  modifier cette demande.")
    if request.method == 'POST':
        form = FundingRequestForm(request.POST, request.FILES, instance=fr)
        if form.is_valid():
            fr = form.save()
            docs = request.FILES.getlist('optional_docs')
            if docs:
                fr.add_funding_docs(docs)
            UserActionLog.record(
                request=request,
                action=UserActionLog.ACTION_UPDATE,
                obj=fr,
                metadata={'updated_fields': list(form.changed_data), 'documents_added': len(docs)},
            )
            messages.success(request, "Demande mise Ã  jour.")
            return redirect('funding_request_details_public', public_id=fr.public_id)
    else:
        form = FundingRequestForm(instance=fr)
    return render(request, 'page/add_funding_request.html', {'form': form, 'update': True})


@login_required
def delete_funding_request(request, public_id):
    fr = FundingRequest.objects.filter(public_id=public_id).first()
    if not fr or fr.created_by != request.user:
        return HttpResponseForbidden("Vous n'Ãªtes pas autorisÃ© Ã  supprimer cette demande.")
    if request.method == 'POST':
        fr.delete()
        UserActionLog.record(
            request=request,
            action=UserActionLog.ACTION_DELETE,
            obj=fr,
            metadata={'type': 'funding_request'},
        )
        messages.success(request, "Demande supprimÃ©e.")
        return redirect('profile')
    return render(request, 'page/confirm_delete.html', {'object': fr, 'type': 'funding_request'})


@login_required
@require_POST
def close_funding_request(request, public_id):
    """ClÃ´turer une demande de financement (marquer comme terminÃ©e)"""
    fr = FundingRequest.objects.filter(public_id=public_id).first()
    if not fr or fr.created_by != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': "Vous n'Ãªtes pas autorisÃ© Ã  clÃ´turer cette demande."}, status=403)
        return HttpResponseForbidden("Vous n'Ãªtes pas autorisÃ© Ã  clÃ´turer cette demande.")

    # Trouver le statut "Clos" ou "TerminÃ©"
    closed_status = _resolve_or_create_status(
        FundingRequestStatus,
        fallback_name="Clos",
        fallback_description="Statut de clôture de demande de financement.",
        keywords=("clos", "cloture", "termine"),
    )
    if closed_status:
        previous_status = fr.funding_request_status_name
        fr.funding_request_status = closed_status
        fr.save(update_fields=['funding_request_status', 'updated_at'])
        UserActionLog.record(
            request=request,
            action=UserActionLog.ACTION_CLOSE,
            obj=fr,
            metadata={'previous_status': previous_status, 'new_status': closed_status.name},
        )
        messages.success(request, "Demande de financement clÃ´turÃ©e avec succÃ¨s.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Demande clÃ´turÃ©e avec succÃ¨s.', 'new_status': closed_status.name})
    else:
        messages.error(request, "Statut 'Clos' non trouvÃ©. Veuillez contacter un administrateur.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': "Statut 'Clos' non trouvÃ©."}, status=400)

    return redirect('funding_request_details_public', public_id=fr.public_id)


@login_required
@require_POST
def close_loss_alert(request, public_id):
    """ClÃ´turer une alerte de perte (marquer comme trouvÃ©/rÃ©solu)"""
    alert = LossAlert.objects.filter(public_id=public_id).first()
    if not alert or alert.created_by != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': "Vous n'Ãªtes pas autorisÃ© Ã  clÃ´turer cette alerte."}, status=403)
        return HttpResponseForbidden("Vous n'Ãªtes pas autorisÃ© Ã  clÃ´turer cette alerte.")

    # Trouver le statut "TrouvÃ©" ou "RÃ©solu" ou "RetrouvÃ©" ou "Clos"
    found_status = _resolve_or_create_status(
        LossAlertStatus,
        fallback_name="Trouvé",
        fallback_description="Statut de résolution d'alerte de perte.",
        keywords=("trouve", "retrouve", "resolu", "clos"),
    )
    if found_status:
        previous_status = alert.status_alert_name
        alert.loss_alert_status = found_status
        alert.save(update_fields=['loss_alert_status', 'updated_at'])
        UserActionLog.record(
            request=request,
            action=UserActionLog.ACTION_CLOSE,
            obj=alert,
            metadata={'previous_status': previous_status, 'new_status': found_status.name},
        )
        messages.success(request, "Alerte clÃ´turÃ©e avec succÃ¨s. Merci d'avoir tenu SOS GuinÃ©e informÃ© !")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Alerte clÃ´turÃ©e avec succÃ¨s.', 'new_status': found_status.name})
    else:
        messages.error(request, "Statut 'TrouvÃ©' non trouvÃ©. Veuillez contacter un administrateur.")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': "Statut 'TrouvÃ©' non trouvÃ©."}, status=400)

    return redirect('loss_alert_detail_public', public_id=alert.public_id)



@login_required
def edit_funding_request(request, public_id):
    fr = FundingRequest.objects.filter(public_id=public_id).first()
    if not fr or fr.created_by != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à modifier cette demande.")
    if request.method == 'POST':
        form = FundingRequestForm(request.POST, request.FILES, instance=fr)
        if form.is_valid():
            fr = form.save()
            docs = request.FILES.getlist('optional_docs')
            if docs:
                fr.add_funding_docs(docs)
            messages.success(request, "Demande mise à jour.")
            return redirect('funding_request_details_public', public_id=fr.public_id)
    else:
        form = FundingRequestForm(instance=fr)
    return render(request, 'page/add_funding_request.html', {'form': form, 'update': True})


@login_required
def delete_funding_request(request, public_id):
    fr = FundingRequest.objects.filter(public_id=public_id).first()
    if not fr or fr.created_by != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à supprimer cette demande.")
    if request.method == 'POST':
        fr.delete()
        messages.success(request, "Demande supprimée.")
        return redirect('profile')
    return render(request, 'page/confirm_delete.html', {'object': fr, 'type': 'funding_request'})

def add_loss_alert(request):
    if request.method == 'POST':
        form = LossAlertForm(request.POST, request.FILES)
        identifier = (request.POST.get("email") or request.POST.get("phone") or "").strip()
        if _is_rate_limited("add-loss-alert", request, identifier=identifier, limit=3, window=3600):
            form.add_error(None, PUBLIC_RATE_LIMIT_MESSAGE)
            context = {'form': form}
            context.update(_captcha_context())
            return render(request, 'page/add_loss_alert.html', context)
        captcha_ok, captcha_error = verify_turnstile_request(request)
        if not captcha_ok:
            form.add_error(None, captcha_error)
        elif form.is_valid():
            lossAlert = LossAlertService.create_loss_alert_from_form(request, form, identifier)
            
<<<<<<< HEAD
            email_template ='page/template_email/add_loss_alert_email.html'
            
            to_email = [lossAlert.email,]
            email_subject = 'Ajout alerte'
            context = {
                    'name': lossAlert.name,
                    'type': lossAlert.loss_alert_type.name if lossAlert.loss_alert_type else '',
                    'description': lossAlert.description,
                    'email': lossAlert.email,
                    'phone': lossAlert.phone,
                    'country': lossAlert.country,
                    'region': str(lossAlert.region) if lossAlert.region else '',
                    'prefecture': str(lossAlert.prefecture) if lossAlert.prefecture else '',
                    'commune': str(lossAlert.commune) if lossAlert.commune else '',
                    'quarter': str(lossAlert.quarter) if lossAlert.quarter else '',
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
=======
            if identifier:
                cache.delete(_rate_limit_key("add-loss-alert", request, identifier))
>>>>>>> chore/security-design-hardening
          
            return render(request, 'page/confirmation_page/confirmation_loss_alert_added.html',{'request': 'added'} )
        else:
            errors = form.errors
            context = {'form': form}
            context.update(_captcha_context())
            return render(request, 'page/add_loss_alert.html', context)
    else:
        form = LossAlertForm()
    context = {'form': form}
    context.update(_captcha_context())
    return render(request, 'page/add_loss_alert.html', context)

<<<<<<< HEAD

@login_required
def edit_loss_alert(request, public_id):
    alert = LossAlert.objects.filter(public_id=public_id).first()
    if not alert or alert.created_by != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à modifier cette alerte.")
    if request.method == 'POST':
        form = LossAlertForm(request.POST, request.FILES, instance=alert)
        if form.is_valid():
            alert = form.save()
            docs = request.FILES.getlist('optional_docs')
            if docs:
                alert.add_docs(docs)
            messages.success(request, "Alerte mise à jour.")
            return redirect('loss_alert_detail_public', public_id=alert.public_id)
    else:
        form = LossAlertForm(instance=alert)
    return render(request, 'page/add_loss_alert.html', {'form': form, 'update': True})


@login_required
def delete_loss_alert(request, public_id):
    alert = LossAlert.objects.filter(public_id=public_id).first()
    if not alert or alert.created_by != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à supprimer cette alerte.")
    if request.method == 'POST':
        alert.delete()
        messages.success(request, "Alerte supprimée.")
        return redirect('profile')
    return render(request, 'page/confirm_delete.html', {'object': alert, 'type': 'alert'})

def funding_request_detail(request, pk=None, public_id=None):
    if pk is not None:
        funding_request = get_object_or_404(FundingRequest, pk=pk)
        return redirect('funding_request_details_public', public_id=funding_request.public_id, permanent=True)
    else:
        funding_request = get_object_or_404(FundingRequest, public_id=public_id)
=======
>>>>>>> chore/security-design-hardening

@login_required
def edit_loss_alert(request, public_id):
    alert = LossAlert.objects.filter(public_id=public_id).first()
    if not alert or alert.created_by != request.user:
        return HttpResponseForbidden("Vous n'Ãªtes pas autorisÃ© Ã  modifier cette alerte.")
    if request.method == 'POST':
        form = LossAlertForm(request.POST, request.FILES, instance=alert)
        if form.is_valid():
            alert = form.save()
            docs = request.FILES.getlist('optional_docs')
            if docs:
                alert.add_docs(docs)
            UserActionLog.record(
                request=request,
                action=UserActionLog.ACTION_UPDATE,
                obj=alert,
                metadata={'updated_fields': list(form.changed_data), 'documents_added': len(docs)},
            )
            messages.success(request, "Alerte mise Ã  jour.")
            return redirect('loss_alert_detail_public', public_id=alert.public_id)
    else:
        form = LossAlertForm(instance=alert)
    return render(request, 'page/add_loss_alert.html', {'form': form, 'update': True})


@login_required
def delete_loss_alert(request, public_id):
    alert = LossAlert.objects.filter(public_id=public_id).first()
    if not alert or alert.created_by != request.user:
        return HttpResponseForbidden("Vous n'Ãªtes pas autorisÃ© Ã  supprimer cette alerte.")
    if request.method == 'POST':
        alert.delete()
        UserActionLog.record(
            request=request,
            action=UserActionLog.ACTION_DELETE,
            obj=alert,
            metadata={'type': 'loss_alert'},
        )
        messages.success(request, "Alerte supprimÃ©e.")
        return redirect('profile')
    return render(request, 'page/confirm_delete.html', {'object': alert, 'type': 'alert'})

def funding_request_detail(request, pk=None, public_id=None):
    if pk is not None:
        funding_request = get_object_or_404(FundingRequest, pk=pk)
        return redirect('funding_request_details_public', public_id=funding_request.public_id, permanent=True)
    else:
        funding_request = get_object_or_404(FundingRequest, public_id=public_id)

    # Obtenir tous les commentaires liÃ©s Ã  cet objet
    content_type = ContentType.objects.get_for_model(FundingRequest)
    comments = Comment.objects.filter(content_type=content_type, object_id=funding_request.id).select_related('user')

    comment_form = CommentForm()

    return render(request, 'page/funding_request_details.html', {
        'funding_request': funding_request,
        'comments': comments,  # ðŸ”´ Important !
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

    # Obtenir tous les commentaires liÃ©s Ã  cet objet
    content_type = ContentType.objects.get_for_model(LossAlert)
    comments = Comment.objects.filter(content_type=content_type, object_id=alert.id, isDeleted=False).select_related('user')

    comment_form = CommentForm()

    return render(request, 'page/loss_alert_details.html', {
        'alert': alert,
        'comments': comments,  # ðŸ”´ Important !
        'comment_form': comment_form,
        'model_name': 'lossalert',
        'object_id': alert.id
    })

def contact(request):
    contact = MessageContactForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST':
        name = request.POST.get('name')
        email = (request.POST.get('email') or '').strip()
        message = request.POST.get('message')
<<<<<<< HEAD
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
=======
        if _is_rate_limited("contact", request, identifier=email, limit=5, window=3600):
            contact.add_error(None, PUBLIC_RATE_LIMIT_MESSAGE)
        else:
            captcha_ok, captcha_error = verify_turnstile_request(request)
            if not captcha_ok:
                contact.add_error(None, captcha_error)
            elif contact.is_valid():
                contact.save()
                context = {
                    'name': name,
                    'email': email,
                    'message': message,
                }
                template_email = 'page/template_email/contact_form_email.html'
                to_email = [email,]
                mail_subject = "Message de contact"
                try:
                    EmailService.send_template_email(to_email, mail_subject, template_email, context)
                except Exception as e:
                    logger.warning("Email de contact non envoye, message conserve en base: %s", e)
                else:
                    if email:
                        cache.delete(_rate_limit_key("contact", request, email))
                contact = MessageContactForm()
                context = {'success': 'Votre message a été reçu avec succès.', 'form': contact}
                context.update(_captcha_context())
                return render(request, 'page/contact.html', context)
    context = {'form': contact}
    context.update(_captcha_context())
    return render(request, 'page/contact.html', context)
>>>>>>> chore/security-design-hardening

def thanks(request):
    return render(request, 'page/thanks.html')


def donation(request):
    initial = _prefill_donor_initial_data(request)
    form = DonationForm(request.POST or None, initial=initial)
    if request.method == 'POST':

        identifier = (request.POST.get("donor_email") or request.POST.get("donor_phone") or "").strip()
        if _is_rate_limited("donation", request, identifier=identifier, limit=5, window=3600):
            form.add_error(None, PUBLIC_RATE_LIMIT_MESSAGE)
            context = {'form': form}
            context.update(_captcha_context())
            return render(request, 'page/donation.html', context)
        captcha_ok, captcha_error = verify_turnstile_request(request)
        if not captcha_ok:
            form.add_error(None, captcha_error)
            context = {'form': form}
            context.update(_captcha_context())
            return render(request, 'page/donation.html', context)
        if not form.is_valid():

            errors = form.errors

            context = {'form': form, 'errors': errors}
            context.update(_captcha_context())
            return render(request, 'page/donation.html', context)

        # RÃ©cupÃ©rer les donnÃ©es du formulaire

        amount = form.cleaned_data['amount']
        user_email = form.cleaned_data['donor_email']
        donor_first_name = form.cleaned_data['donor_first_name']
        donor_last_name = form.cleaned_data['donor_last_name']
        donor_country = form.cleaned_data['donor_country']
        donor_city = form.cleaned_data['donor_city']
        donor_phone = form.cleaned_data['donor_phone']
        donor_address = form.cleaned_data['donor_address']
        try:
            # Enregistrer le paiement dans la base de donnÃ©es
            payment = Donation.objects.create(
                amount=amount,
                donor_email=user_email,
                donor_first_name= donor_first_name,
                donor_last_name= donor_last_name,
                donor_address= donor_address,
                donor_city=donor_city,
                donor_country=donor_country,
                donor_phone =donor_phone,
                transaction_id=str(uuid.uuid4()),  # GÃ©nÃ©rer un ID de transaction unique
                #reference=data.get('reference')
            )

            # Initialize Djomy Gateway for Donations
            try:
<<<<<<< HEAD
                print("sending email")
                EmailService.send_template_email(to_email, mail_subject, template_email, context)
                print("email sent")
            except Exception as e:
                print("email not sent", e)
                messages.error(request, "L'envoi du mail a échoué. Veuillez contacter l'administrateur.")
                return  render(request, 'page/donation.html', {'form': form})
=======
                from django_djomy.services import DjomyService
                ds = DjomyService()
                ref = f"DON_{payment.transaction_id}"
                payment.reference = ref
                payment.save(update_fields=["reference", "updated_at"])
>>>>>>> chore/security-design-hardening

                # Construit l'URL de retour locale dynamique
                callback_url = _build_public_absolute_uri(
                    request,
                    reverse('djomy_payment_callback', kwargs={'payment_id': payment.id, 'type': 'Don'})
                )
                callback_url = f"{callback_url}?token={payment.transaction_id}"
                cancel_url = _build_public_absolute_uri(request, reverse('donation'))
                
                response_data = ds.init_gateway_payment(
                    amount=int(amount),
                    reference=ref,
                    phone=donor_phone,
                    country="GN",
                    return_url=callback_url,
                    cancel_url=cancel_url
                )
                payment_url = _extract_djomy_redirect_url(response_data)
                _log_payment_event(
                    "donation_gateway_initialized",
                    payment_id=payment.id,
                    reference=ref,
                    amount=amount,
                    has_payment_url=bool(payment_url),
                    provider="djomy",
                )
                if not payment_url:
                    messages.error(request, "Url de paiement introuvable dans la réponse de Djomy.")
                    context = {'form': form}
                    context.update(_captcha_context())
                    return render(request, 'page/donation.html', context)
            except Exception as e:
                _log_payment_event(
                    "donation_gateway_error",
                    amount=amount,
                    donor_email=user_email,
                    error=str(e),
                    provider="djomy",
                )
                messages.error(request, "Erreur de communication avec l'API Djomy.")
                # Erreur API Djomy
                context = {'form': form}
                context.update(_captcha_context())
                return render(request, 'page/donation.html', context)

            # Redirige vers la page de paiement de Djomy
            _log_payment_event(
                "donation_redirect_to_gateway",
                payment_id=payment.id,
                reference=payment.reference,
                redirect_url=payment_url,
                provider="djomy",
            )
            return redirect(payment_url)
            
        except Exception as e:
            messages.error(request, "Erreur interne système. Réessayez plus tard.")
            # Erreur interne transaction
            context = {'form': form}
            context.update(_captcha_context())
            return render(request, 'page/donation.html', context)

    context = {'form': form}
    context.update(_captcha_context())
    return render(request, 'page/donation.html', context)

def messageContact(request):
    if request.method == 'POST':

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
<<<<<<< HEAD
                print("sending email")
                EmailService.send_template_email(to_email, mail_subject, template_email, context)

                print("email sent")
            except Exception as e:
                print("email not sent", e)
                return JsonResponse({'error': 'L\'envoi du mail a échoué. Veuillez contacter l\'administrateur.'})
            return JsonResponse( {'success': 'Le message a été envoyé.'})
=======

                EmailService.send_template_email(to_email, mail_subject, template_email, context)


            except Exception as e:

                return JsonResponse({'error': 'L\'envoi du mail a Ã©chouÃ©. Veuillez contacter l\'administrateur.'})
            return JsonResponse( {'success': 'Le message a Ã©tÃ© envoyÃ©.'})
>>>>>>> chore/security-design-hardening
        else :
            errors = contact.errors

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
        
        # RÃ©cupÃ¨re les filtres Ã  partir des paramÃ¨tres GET
        status = request.GET.get('status')
        funding_type = request.GET.get('funding_type')
        min_amount = request.GET.get('min_amount')
        max_amount = request.GET.get('max_amount')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        beneficiary_name = request.GET.get('beneficiary_name')
        
        funding_list = FundingRequest.objects.all()  # RÃ©cupÃ¨re tous les Ã©lÃ©ments
        
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
            
        page_number = request.GET.get('page', 1)  # NumÃ©ro de la page Ã  partir des paramÃ¨tres GET, par dÃ©faut 1
        items_per_page = request.GET.get('items_per_page', 10)  # Nombre d'Ã©lÃ©ments par page, par dÃ©faut 10

        # CrÃ©ation du paginator
        paginator = Paginator(funding_list, items_per_page)
        try:
            page_obj = paginator.page(page_number)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        # PrÃ©pare les donnÃ©es pour le format JSON
        data = {
            'funding_requests': [
                {
                    'title': element.title,
                    'beneficiary_name': element.beneficiary_name,
                    'description_needs': element.description_needs,
                    'funding_request_type_name': element.funding_request_type_name,
                    'funding_request_status': element.funding_request_status_name,  # Utilise la propriÃ©tÃ© funding_request_status_name
                    'principal_image_url': element.principal_image.url if element.principal_image else '',
                    'id': element.id,
                    'public_id': str(element.public_id),
<<<<<<< HEAD
                    'progress': element.progress,  # Utilise la propriété progress
                    'days_remaining': element.days_remaining,  # Utilise la propriété days_remaining
                    'amount': element.funding_amount,
                    'details_url': "/funding-request-details/"+str(element.public_id)+"/",          
=======
                    'progress': element.progress,  # Utilise la propriÃ©tÃ© progress
                    'days_remaining': element.days_remaining,  # Utilise la propriÃ©tÃ© days_remaining
                    'amount': element.funding_amount,
                    'amount_received': element.amount_received,
                    'remaining_amount': element.remaining_amount,
                    'can_fund': element.funding_request_status_name == "En cours",
                    'details_url': "/funding-request-details/"+str(element.public_id)+"/",
                    'payment_url': "/funding/"+str(element.public_id)+"/djomy/",
                    'is_creator': request.user.is_authenticated and element.created_by_id == request.user.id,
                    'close_url': "/funding-request/"+str(element.public_id)+"/close/",
>>>>>>> chore/security-design-hardening
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
                    'description': element.description,
                    'status_alert_name': element.status_alert_name,  # Utilise la propriété status_alert_name
                    'principal_image_url': element.principal_image.url if element.principal_image else '',
                    'type_alert_name': element.type_alert_name,  # Utilise la propriété type_alert_name
                    'date_alert': element.date_alert,
                    'hour_alert': element.hour_alert,
                    'region': str(element.region) if element.region else '',
                    'prefecture': str(element.prefecture) if element.prefecture else '',
                    'commune': str(element.commune) if element.commune else '',
                    'quarter': str(element.quarter) if element.quarter else '',
                    'address': element.address or '',
                    'id': element.id,
                    'public_id': str(element.public_id),
<<<<<<< HEAD
                    'details_url': "/loss-alert-details/"+str(element.public_id)+"/",  # URL des détails de l'alerte
=======
                    'details_url': "/loss-alert-details/"+str(element.public_id)+"/",  # URL des dÃ©tails de l'alerte
                    'phone': element.phone or '',
                    'is_creator': request.user.is_authenticated and element.created_by_id == request.user.id,
                    'close_url': "/loss-alert/"+str(element.public_id)+"/close/",
>>>>>>> chore/security-design-hardening
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

<<<<<<< HEAD
def paycard_funding(request, pk=None, public_id=None):
    if pk is not None:
        funding_request = get_object_or_404(FundingRequest, pk=pk)
        return redirect('paycard_funding_public', public_id=funding_request.public_id, permanent=True)
=======
def djomy_funding(request, pk=None, public_id=None):
    if pk is not None:
        funding_request = get_object_or_404(FundingRequest, pk=pk)
        return redirect('djomy_funding_public', public_id=funding_request.public_id, permanent=True)
>>>>>>> chore/security-design-hardening
    else:
        funding_request = get_object_or_404(FundingRequest, public_id=public_id)
    if not funding_request:
        messages.error(request, "Demande de financement non trouvée.")
        return redirect('djomy_funding', pk)
    if request.method == 'POST':
        return start_djomy_funding_payment(request, funding_public_id=funding_request.public_id)
    form = FundingPaymentForm(initial=_prefill_donor_initial_data(request))
    context = {'funding_request': funding_request, 'form': form}
    context.update(_captcha_context())
    return render(request, 'page/funding_payment.html', context)


@csrf_protect
<<<<<<< HEAD
def start_paycard_funding_payment(request, funding_id=None, funding_public_id=None):
=======
def start_djomy_funding_payment(request, funding_id=None, funding_public_id=None):
>>>>>>> chore/security-design-hardening
    if funding_id is not None:
        funding_request = FundingRequest.objects.filter(id=funding_id).first()
    else:
        funding_request = FundingRequest.objects.filter(public_id=funding_public_id).first()

    if not funding_request:
        messages.error(request, "Demande de financement non trouvée.")
        return redirect('funding_request_list')
    initial = _prefill_donor_initial_data(request)
    form = FundingPaymentForm(request.POST or None, initial=initial)
    if request.method == 'POST':
        identifier = (request.POST.get("donor_email") or request.POST.get("donor_phone") or "").strip()
        if _is_rate_limited("funding-payment", request, identifier=identifier, limit=5, window=3600):
            form.add_error(None, PUBLIC_RATE_LIMIT_MESSAGE)
            context = {'funding_request': funding_request, 'form': form}
            context.update(_captcha_context())
            return render(request, 'page/funding_payment.html', context)
        captcha_ok, captcha_error = verify_turnstile_request(request)
        if not captcha_ok:
            form.add_error(None, captcha_error)
            context = {'funding_request': funding_request, 'form': form}
            context.update(_captcha_context())
            return render(request, 'page/funding_payment.html', context)
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
                amount_decimal = Decimal(str(amount))
            except (InvalidOperation, TypeError, ValueError):
                form.add_error('amount', "Montant invalide.")
                context = {'funding_request': funding_request, 'form': form}
                context.update(_captcha_context())
                return render(request, 'page/funding_payment.html', context)
            if amount_decimal > funding_request.remaining_amount:
                form.add_error('amount', "Le montant ne doit pas dépasser le reste à payer.")
                context = {'funding_request': funding_request, 'form': form}
                context.update(_captcha_context())
                return render(request, 'page/funding_payment.html', context)
            try:
                # Enregistrer le paiement dans la base de donnÃ©es
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
                    transaction_id=str(uuid.uuid4()),  # GÃ©nÃ©rer un ID de transaction unique
                    #reference=data.get('reference')
                )

                # Initialize Djomy Gateway for Funding
                try:
<<<<<<< HEAD
                    print("sending email")
                    EmailService.send_template_email(to_email, mail_subject, template_email, context)
                    print("email sent")
                except Exception as e:
                    print("email not sent", e)
                    messages.error(request, "L'envoi du mail a échoué. Veuillez contacter l'administrateur.")
                    return  render(request, 'page/funding_payment.html', {'funding_request': funding_request, 'form': form})
=======
                    from django_djomy.services import DjomyService
                    ds = DjomyService()
                    ref = f"FUND_{payment.transaction_id}"
                    payment.reference = ref
                    payment.save(update_fields=["reference", "updated_at"])
                    
                    # Construit l'URL de retour locale dynamique
                    callback_url = _build_public_absolute_uri(
                        request,
                        reverse('djomy_payment_callback', kwargs={'payment_id': payment.id, 'type': 'Financement'})
                    )
                    callback_url = f"{callback_url}?token={payment.transaction_id}"
                    cancel_url = _build_public_absolute_uri(
                        request,
                        reverse('funding_request_details_public', kwargs={'public_id': funding_request.public_id})
                    )
                    
                    response_data = ds.init_gateway_payment(
                        amount=int(amount),
                        reference=ref,
                        phone=donor_phone,
                        country="GN",
                        return_url=callback_url,
                        cancel_url=cancel_url
                    )
                    payment_url = _extract_djomy_redirect_url(response_data)
                    _log_payment_event(
                        "funding_gateway_initialized",
                        payment_id=payment.id,
                        reference=ref,
                        funding_public_id=str(funding_request.public_id),
                        amount=amount,
                        has_payment_url=bool(payment_url),
                        provider="djomy",
                    )
                    if not payment_url:
                        messages.error(request, "Url de paiement introuvable dans la réponse de Djomy.")
                        context = {'funding_request': funding_request, 'form': form}
                        context.update(_captcha_context())
                        return render(request, 'page/funding_payment.html', context)
                except Exception as e:
                    _log_payment_event(
                        "funding_gateway_error",
                        funding_public_id=str(funding_request.public_id),
                        amount=amount,
                        donor_email=user_email,
                        error=str(e),
                        provider="djomy",
                    )
                    messages.error(request, "Erreur de communication avec l'API Djomy.")
                    # Erreur API Djomy
                    context = {'funding_request': funding_request, 'form': form}
                    context.update(_captcha_context())
                    return render(request, 'page/funding_payment.html', context)
>>>>>>> chore/security-design-hardening

                # Redirige vers Djomy !
                _log_payment_event(
                    "funding_redirect_to_gateway",
                    payment_id=payment.id,
                    reference=payment.reference,
                    funding_public_id=str(funding_request.public_id),
                    redirect_url=payment_url,
                    provider="djomy",
                )
                return redirect(payment_url)
                
            except Exception as e:
                messages.error(request, "Erreur interne système. Réessayez plus tard.")
                # Erreur interne transaction
                context = {'funding_request': funding_request, 'form': form}
                context.update(_captcha_context())
                return render(request, 'page/funding_payment.html', context)

        else:
            context = {'funding_request': funding_request, 'form': form}
            context.update(_captcha_context())
            return render(request, 'page/funding_payment.html', context)

    if funding_request and funding_request.public_id:
        return redirect('djomy_funding_public', public_id=funding_request.public_id)
    return redirect('funding_request_list')


<<<<<<< HEAD
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
=======
@require_GET
def djomy_payment_callback(request, payment_id=None, type=None, payment_public_id=None):
    payment_type = (type or "").strip().lower()
    token = (request.GET.get("token") or "").strip()
    model = Donation if payment_type == "don" else FundPayment if payment_type == "financement" else None

    if model is None:
        return HttpResponseForbidden("Type de paiement invalide.")

    if payment_id is not None:
        payment = model.objects.filter(id=payment_id).first()
    else:
        payment = model.objects.filter(public_id=payment_public_id).first()

    if not _is_valid_payment_callback_token(payment, token):
        return HttpResponseForbidden("Callback paiement invalide.")

    _log_payment_event(
        "payment_callback_received",
        payment_type=payment_type,
        payment_id=getattr(payment, "id", None),
        payment_public_id=str(getattr(payment, "public_id", "") or ""),
        provider="djomy",
    )

    success_status = _get_payment_success_status(payment)

    if payment.status == "en_attente":
        payment.status = success_status
        payment.save(update_fields=["status", "updated_at"])

        if model is FundPayment and getattr(payment, "funding_request_id", None):
            funding_request = payment.funding_request
            funding_request.amount_received = (funding_request.amount_received or 0) + payment.amount
            funding_request.save(update_fields=["amount_received", "updated_at"])
            _finalize_funding_request_status(funding_request)

        _send_payment_success_email(payment)

    return render(request, 'page/confirmation_page/confirmation_payment.html', {'request': 'added', 'type': type})


@csrf_exempt
@require_POST
def djomy_webhook(request):
    if not _verify_djomy_webhook_signature(request):
        _log_payment_event("payment_webhook_rejected", reason="invalid_signature", provider="djomy")
        return HttpResponseForbidden("Signature webhook invalide.")

    try:
        payload = json.loads((request.body or b"{}").decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Payload JSON invalide."}, status=400)

    model, payment, reference, tx_id = _resolve_webhook_payment(payload)
    if payment is None:
        _log_payment_event(
            "payment_webhook_unmatched",
            reference=reference,
            transaction_id=tx_id,
            provider="djomy",
        )
        logger.warning("Webhook Djomy reÃ§u sans paiement correspondant: %s", payload)
        return JsonResponse({"ok": True, "ignored": True, "reason": "payment_not_found"}, status=200)

    status_raw = _extract_first_non_empty(
        payload,
        ("status", "payment_status", "transaction_status", "state"),
    )
    if status_raw is None:
        status_raw = _extract_first_non_empty(payload, ("event", "event_type", "type", "name"))
    normalized_status = _normalize_payment_status(status_raw)
    _log_payment_event(
        "payment_webhook_received",
        payment_type="funding" if model is FundPayment else "donation",
        payment_id=payment.id,
        reference=reference or payment.reference,
        transaction_id=tx_id or payment.transaction_id,
        normalized_status=normalized_status,
        provider="djomy",
    )

    previous_status = payment.status
    update_fields = []

    if reference and not payment.reference:
        payment.reference = reference
        update_fields.append("reference")
    if tx_id and not payment.transaction_id:
        payment.transaction_id = tx_id
        update_fields.append("transaction_id")

    allowed_statuses = {choice[0] for choice in payment._meta.get_field("status").choices}
    if normalized_status in allowed_statuses and payment.status != normalized_status:
        payment.status = normalized_status
        update_fields.append("status")

    if update_fields:
        update_fields.append("updated_at")
        payment.save(update_fields=update_fields)

    success_status = _get_payment_success_status(payment)

    # Idempotence: incrementer une seule fois le montant reçu lors du passage à "réussi".
    if model is FundPayment and previous_status != success_status and payment.status == success_status:
        funding_request = payment.funding_request
        funding_request.amount_received = (funding_request.amount_received or 0) + payment.amount
        funding_request.save(update_fields=["amount_received", "updated_at"])
        _finalize_funding_request_status(funding_request)
        _send_payment_success_email(payment)
    elif model is Donation and previous_status != success_status and payment.status == success_status:
        _send_payment_success_email(payment)

    return JsonResponse(
        {
            "ok": True,
            "payment_type": "funding" if model is FundPayment else "donation",
            "payment_id": payment.id,
            "status": payment.status,
        },
        status=200,
    )
>>>>>>> chore/security-design-hardening


@login_required
@require_POST
def add_comment(request, model_name, object_id):
<<<<<<< HEAD
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
                html = render_to_string(
                    'page/components/comments/comment_item.html',
                    {'comment': comment, 'user': request.user}
                )
                return JsonResponse({
                    'success': True,
                    'comment_html': html,
                    'comment': {
                        'user': comment.user.username,
                        'text': comment.text,
                        'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
                    }
                })
            else:
                return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Requête invalide'})
=======
    model_key = (model_name or "").lower()
    model_cls = ALLOWED_COMMENT_MODELS.get(model_key)
    if model_cls is None:
        return JsonResponse({'success': False, 'message': 'Modele non autorise'}, status=400)
    rate_identifier = f"{request.user.id}:{model_key}:{object_id}"
    if _is_rate_limited("add-comment", request, identifier=rate_identifier, limit=8, window=300):
        return JsonResponse({'success': False, 'message': PUBLIC_RATE_LIMIT_MESSAGE}, status=429)
>>>>>>> chore/security-design-hardening

    target = model_cls.objects.filter(id=object_id).first()
    if target is None:
        return JsonResponse({'success': False, 'message': 'Objet introuvable'}, status=404)

    form = CommentForm(request.POST)
    if form.is_valid():
        content_type = ContentType.objects.get_for_model(model_cls)
        comment = form.save(commit=False)
        comment.user = request.user
        comment.content_type = content_type
        comment.object_id = target.id
        comment.save()
        cache.delete(_rate_limit_key("add-comment", request, rate_identifier))
        html = render_to_string(
            'page/components/comments/comment_item.html',
            {'comment': comment, 'user': request.user}
        )
        return JsonResponse({
            'success': True,
            'comment_html': html,
            'comment': {
                'user': comment.user.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
            }
        })
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)



def reply_comment(request):
    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('text')
        parent_id = request.POST.get('parent')
        rate_identifier = f"{request.user.id}:{parent_id}"
        if _is_rate_limited("reply-comment", request, identifier=rate_identifier, limit=8, window=300):
            return JsonResponse({'success': False, 'message': PUBLIC_RATE_LIMIT_MESSAGE}, status=429)
        parent = get_object_or_404(Comment, id=parent_id)
        comment = Comment.objects.create(
            user=request.user,
            content_object=parent.content_object,
            parent=parent,
            text=text
        )
        cache.delete(_rate_limit_key("reply-comment", request, rate_identifier))
        html = render_to_string('page/components/comments/comment_item.html', {'comment': comment, 'user': request.user})
        return JsonResponse({'success': True, 'reply_html': html})
    return JsonResponse({'success': False}, status=400)

@login_required
@require_POST
def edit_comment(request, comment_id):
    try:
        comment = Comment.objects.get(id=comment_id, user=request.user)
    except Comment.DoesNotExist:
<<<<<<< HEAD
        return JsonResponse({'success': False, 'error': 'Commentaire non trouvé'}, status=404)
=======
        return JsonResponse({'success': False, 'error': 'Commentaire non trouvÃ©'}, status=404)
>>>>>>> chore/security-design-hardening
    # Support both form-encoded and JSON payloads
    new_text = ''
    if request.content_type and 'application/json' in request.content_type:
        import json
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
            new_text = (payload.get('text') or '').strip()
        except Exception:
            new_text = ''
    else:
        new_text = (request.POST.get('text') or '').strip()
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
<<<<<<< HEAD
        if comment.user_id == request.user.id:
            return JsonResponse({'success': False, 'error': 'Vous ne pouvez pas signaler votre propre commentaire'}, status=400)
        # Optionnel : logguer ou sauvegarder dans une table Report si nécessaire
        print(f"Commentaire signalé par {request.user.username}: {comment.text}")
        return JsonResponse({'success': True, 'message': 'Le commentaire a été signalé'})
=======
        rate_identifier = f"{request.user.id}:{comment_id}"
        if _is_rate_limited("report-comment", request, identifier=rate_identifier, limit=10, window=3600):
            return JsonResponse({'success': False, 'error': PUBLIC_RATE_LIMIT_MESSAGE}, status=429)
        if comment.user_id == request.user.id:
            return JsonResponse({'success': False, 'error': 'Vous ne pouvez pas signaler votre propre commentaire'}, status=400)
        reason = (request.POST.get('reason') or request.POST.get('message') or 'Signalement utilisateur').strip()
        try:
            Report.objects.create(comment=comment, reporter=request.user, reason=reason[:500])
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'Vous avez deja signale ce commentaire'}, status=400)
        cache.delete(_rate_limit_key("report-comment", request, rate_identifier))
        UserActionLog.record(
            request=request,
            action=UserActionLog.ACTION_CREATE,
            obj=comment,
            metadata={'report_reason': reason[:500], 'reported_comment_id': comment.id},
        )
        return JsonResponse({'success': True, 'message': 'Le commentaire a ete signale'})
>>>>>>> chore/security-design-hardening
    except Comment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Commentaire introuvable'}, status=404)

# --- Location dependent lists (JSON) ---
def prefectures_by_region(request):
    region_id = request.GET.get('region')
    data = []
    if region_id:
        try:
            from .models import Prefecture
            qs = Prefecture.objects.filter(region_id=region_id).order_by('name')
            data = [{'id': p.id, 'name': p.name} for p in qs]
        except Exception:
            data = []
    return JsonResponse({'results': data})


<<<<<<< HEAD




# --- Location dependent lists (JSON) ---
def prefectures_by_region(request):
    region_id = request.GET.get('region')
    data = []
    if region_id:
        try:
            from .models import Prefecture
            qs = Prefecture.objects.filter(region_id=region_id).order_by('name')
            data = [{'id': p.id, 'name': p.name} for p in qs]
        except Exception:
            data = []
    return JsonResponse({'results': data})


=======
>>>>>>> chore/security-design-hardening
def communes_by_prefecture(request):
    prefecture_id = request.GET.get('prefecture')
    data = []
    if prefecture_id:
        try:
            from .models import Commune
            qs = Commune.objects.filter(prefecture_id=prefecture_id).order_by('name')
            data = [{'id': c.id, 'name': c.name} for c in qs]
        except Exception:
            data = []
    return JsonResponse({'results': data})


def quarters_by_commune(request):
    commune_id = request.GET.get('commune')
    data = []
    if commune_id:
        try:
            from .models import Quarter
            qs = Quarter.objects.filter(commune_id=commune_id).order_by('name')
            data = [{'id': q.id, 'name': q.name} for q in qs]
        except Exception:
            data = []
    return JsonResponse({'results': data})
