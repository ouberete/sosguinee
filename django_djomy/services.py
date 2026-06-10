import hmac
import hashlib
import requests
import json
import logging
from django.conf import settings
from .models import DjomyPayment

logger = logging.getLogger(__name__)

class DjomyService:
    def __init__(self):
        self.base_url = getattr(settings, "DJOMY_BASE_URL", "https://sandbox-api.djomy.africa/v1")
        self.client_id = settings.DJOMY_CLIENT_ID
        self.client_secret = settings.DJOMY_CLIENT_SECRET
        self.timeout = getattr(settings, "DJOMY_REQUEST_TIMEOUT", 12)

    def _generate_x_api_key(self):
        """Génère le header X-API-KEY: clientId:signature"""
        signature = hmac.new(
            self.client_secret.encode('utf-8'),
            self.client_id.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"{self.client_id}:{signature}"

    def get_access_token(self):
        """Récupère le JWT Token via /auth"""
        url = f"{self.base_url}/auth"
        headers = {"X-API-KEY": self._generate_x_api_key()}
        try:
            response = requests.post(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            token = response.json().get('data', {}).get("accessToken")
            if token:
                logger.info("Access token Djomy récupéré avec succès.")
            else:
                logger.warning("Access token absent de la réponse Djomy.")
            return token
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération du token Djomy : {e}")
            return None

    def init_gateway_payment(self, amount, reference, phone, country="GN", return_url=None, cancel_url=None):
        """Initie un paiement avec redirection et l'enregistre en base localement"""
        token = self.get_access_token()
        url = f"{self.base_url}/payments/gateway"
        
        payload = {
            "amount": float(amount),
            "countryCode": country,
            "payerNumber": phone,
            "merchantPaymentReference": reference,
            "returnUrl": return_url if return_url else settings.DJOMY_RETURN_URL,
            "cancelUrl": cancel_url if cancel_url else settings.DJOMY_CANCEL_URL,
            "allowedPaymentMethods": ["OM", "MOMO", "CARD", "PAYCARD"]
        }
        
        headers = {
            "X-API-KEY": self._generate_x_api_key(),
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            res_json = response.json()
            logger.info(f"Paiement Djomy initié avec succès pour la référence : {reference}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'initiation du paiement Djomy : {e}")
            return None
        
        # Enregistrement local
        DjomyPayment.objects.create(
            merchant_reference=reference,
            amount=amount,
            phone=phone,
            payment_url=res_json.get('paymentUrl'),
            status='PENDING'
        )
        
        return res_json

    def verify_webhook_signature(self, raw_payload, received_signature_header):
        """Vérifie la signature HMAC du Webhook"""
        if not received_signature_header or not received_signature_header.startswith('v1:'):
            return False
        
        received_sig = received_signature_header.split('v1:')[1]
        expected_sig = hmac.new(
            self.client_secret.encode('utf-8'),
            raw_payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(received_sig, expected_sig)

    def get_payment_status(self, transaction_id):
        """
        Récupère le détail et le statut d'un paiement spécifique.
        Basé sur : /v1/payments/{transactionId}/status
        """
        token = self.get_access_token()
        url = f"{self.base_url}/payments/{transaction_id}/status"
        
        headers = {
            "X-API-KEY": self._generate_x_api_key(),
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Statut inattendu lors de la récupération du statut Djomy : {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération du statut du paiement Djomy {transaction_id} : {e}")
        return None

    def list_payment_links(self, page=1, limit=10, start_date=None, end_date=None):
        """
        Liste tous les liens de paiement avec filtres optionnels.
        Basé sur : /v1/links
        """
        token = self.get_access_token()
        url = f"{self.base_url}/links"
        
        params = {
            "page": page,
            "limit": limit
        }
        if start_date: params["startDate"] = start_date
        if end_date: params["endDate"] = end_date
        
        headers = {
            "X-API-KEY": self._generate_x_api_key(),
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Statut inattendu lors de la récupération des liens Djomy : {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des liens Djomy : {e}")
        return None
