from datetime import timedelta
from decimal import Decimal
import hashlib
import hmac
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from page.forms import DonationForm, FundingPaymentForm, MultipleFileField
from page.models import Comment, Donation, FundPayment, FundingRequest, LossAlert
from page.tasks import reconcile_pending_payments


class PaymentCallbackTests(TestCase):
    def _funding(self):
        return FundingRequest.objects.create(
            beneficiary_name="Test Beneficiary",
            funding_amount=Decimal("1000.00"),
            description_needs="Need support",
            principal_image="img/Fundings/test.png",
            amount_received=Decimal("0.00"),
        )

    def test_donation_callback_rejects_invalid_token(self):
        donation = Donation.objects.create(
            amount=Decimal("10000"),
            donor_email="donor@example.com",
            transaction_id="tok_valid",
        )
        url = reverse("djomy_payment_callback", kwargs={"payment_id": donation.id, "type": "Don"})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        donation.refresh_from_db()
        self.assertEqual(donation.status, "en_attente")

    def test_donation_callback_does_not_confirm_without_provider_verification(self):
        # Le retour navigateur seul (token valide) ne doit jamais confirmer le
        # paiement: sans vérification Djomy concluante, il reste en attente.
        donation = Donation.objects.create(
            amount=Decimal("10000"),
            donor_email="donor@example.com",
            transaction_id="tok_valid",
        )
        url = reverse("djomy_payment_callback", kwargs={"payment_id": donation.id, "type": "Don"})

        with patch("page.views._verify_payment_status_with_djomy", return_value=None):
            response = self.client.get(f"{url}?token={donation.transaction_id}")
        self.assertEqual(response.status_code, 200)
        donation.refresh_from_db()
        self.assertEqual(donation.status, "en_attente")

    def test_donation_callback_confirms_when_provider_reports_success(self):
        donation = Donation.objects.create(
            amount=Decimal("10000"),
            donor_email="donor@example.com",
            transaction_id="tok_valid",
        )
        url = reverse("djomy_payment_callback", kwargs={"payment_id": donation.id, "type": "Don"})

        with patch("page.views._verify_payment_status_with_djomy", return_value="réussi"):
            response = self.client.get(f"{url}?token={donation.transaction_id}")
        self.assertEqual(response.status_code, 200)
        donation.refresh_from_db()
        self.assertNotEqual(donation.status, "en_attente")

    def test_donation_callback_marks_failure_when_provider_reports_failure(self):
        donation = Donation.objects.create(
            amount=Decimal("10000"),
            donor_email="donor@example.com",
            transaction_id="tok_valid",
        )
        url = reverse("djomy_payment_callback", kwargs={"payment_id": donation.id, "type": "Don"})

        with patch("page.views._verify_payment_status_with_djomy", return_value="échoué"):
            response = self.client.get(f"{url}?token={donation.transaction_id}")
        self.assertEqual(response.status_code, 200)
        donation.refresh_from_db()
        self.assertEqual(donation.status, "échoué")

    def test_funding_callback_updates_received_amount_once(self):
        funding = self._funding()
        payment = FundPayment.objects.create(
            funding_request=funding,
            amount=Decimal("150.00"),
            donor_email="donor@example.com",
            transaction_id="tok_funding",
        )
        url = reverse("djomy_payment_callback", kwargs={"payment_id": payment.id, "type": "Financement"})

        with patch("page.views._verify_payment_status_with_djomy", return_value="réussi"):
            first = self.client.get(f"{url}?token={payment.transaction_id}")
            second = self.client.get(f"{url}?token={payment.transaction_id}")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        funding.refresh_from_db()
        self.assertEqual(funding.amount_received, Decimal("150.00"))

    def test_funding_callback_keeps_amount_above_target(self):
        funding = self._funding()
        payment = FundPayment.objects.create(
            funding_request=funding,
            amount=Decimal("1500.00"),
            donor_email="donor@example.com",
            transaction_id="tok_over_target",
        )
        url = reverse("djomy_payment_callback", kwargs={"payment_id": payment.id, "type": "Financement"})

        with patch("page.views._verify_payment_status_with_djomy", return_value="réussi"):
            response = self.client.get(f"{url}?token={payment.transaction_id}")

        self.assertEqual(response.status_code, 200)
        funding.refresh_from_db()
        self.assertEqual(funding.amount_received, Decimal("1500.00"))
        self.assertEqual(funding.progress, 100)


class FundingPaymentInitiationTests(TestCase):
    def test_initiation_accepts_amount_above_remaining_target(self):
        funding = FundingRequest.objects.create(
            beneficiary_name="Test Beneficiary",
            funding_amount=Decimal("1000.00"),
            description_needs="Need support",
            principal_image="img/Fundings/test.png",
            amount_received=Decimal("0.00"),
        )
        url = reverse(
            "funding_djomy_payment_public",
            kwargs={"funding_public_id": funding.public_id},
        )

        with (
            patch("page.views.verify_turnstile_request", return_value=(True, None)),
            patch("page.views._is_rate_limited", return_value=False),
            patch(
                "django_djomy.services.DjomyService.init_gateway_payment",
                return_value={"paymentUrl": "https://pay.example.test/checkout"},
            ),
        ):
            response = self.client.post(url, {
                "amount": "15000",
                "donor_email": "donor@example.com",
                "donor_phone": "+224600000000",
                "is_anonymous": "on",
            })

        self.assertEqual(response.status_code, 302)
        payment = FundPayment.objects.get(funding_request=funding)
        self.assertEqual(payment.amount, Decimal("15000.00"))


class FundingPaymentAmountValidationTests(TestCase):
    def _form(self, amount):
        return FundingPaymentForm(data={
            "amount": amount,
            "donor_email": "donor@example.com",
            "donor_phone": "+224600000000",
            "is_anonymous": "on",
        })

    def test_positive_integer_amount_is_valid_without_a_target_ceiling(self):
        form = self._form("15000")
        self.assertTrue(form.is_valid(), form.errors)

    def test_amount_below_minimum_is_rejected_server_side(self):
        form = self._form("9999")
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_negative_amount_is_rejected_server_side(self):
        form = self._form("-10000")
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_fractional_gnf_amount_is_rejected_server_side(self):
        form = self._form("10000.50")
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)


class DonationAmountValidationTests(TestCase):
    def _form(self, amount):
        return DonationForm(data={
            "amount": amount,
            "donor_email": "donor@example.com",
            "donor_phone": "+224600000000",
            "is_anonymous": "on",
        })

    def test_positive_integer_donation_is_valid(self):
        form = self._form("10000")
        self.assertTrue(form.is_valid(), form.errors)

    def test_fractional_donation_is_rejected_server_side(self):
        form = self._form("10000.50")
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_donation_below_minimum_is_rejected_server_side(self):
        form = self._form("9999")
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)


class MultipleFileFieldValidationTests(TestCase):
    def test_pdf_with_matching_signature_is_accepted(self):
        field = MultipleFileField(required=False)
        result = field.clean([SimpleUploadedFile("proof.pdf", b"%PDF-1.4 content")])
        self.assertEqual(len(result), 1)

    def test_pdf_extension_with_non_pdf_content_is_rejected(self):
        field = MultipleFileField(required=False)
        with self.assertRaises(ValidationError):
            field.clean([SimpleUploadedFile("proof.pdf", b"MZ executable")])


@override_settings(DEBUG=False, DJOMY_WEBHOOK_SECRET="webhook-test-secret")
class PaymentWebhookAmountTests(TestCase):
    def setUp(self):
        self.funding = FundingRequest.objects.create(
            beneficiary_name="Test Beneficiary",
            funding_amount=Decimal("1000.00"),
            description_needs="Need support",
            principal_image="img/Fundings/test.png",
            amount_received=Decimal("0.00"),
        )
        self.payment = FundPayment.objects.create(
            funding_request=self.funding,
            amount=Decimal("1500.00"),
            donor_email="donor@example.com",
            transaction_id="tok_webhook",
            reference="FUND_tok_webhook",
        )

    def _post_webhook(self, amount):
        payload = {
            "eventType": "payment.success",
            "data": {
                "merchantPaymentReference": self.payment.reference,
                "transactionId": "provider-transaction",
                "amount": amount,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        signature = hmac.new(b"webhook-test-secret", body, hashlib.sha256).hexdigest()
        return self.client.generic(
            "POST",
            reverse("djomy_webhook"),
            body,
            content_type="application/json",
            HTTP_X_DJOMY_SIGNATURE=signature,
        )

    @patch("page.views._send_payment_success_email")
    def test_signed_webhook_confirms_matching_amount_above_target(self, send_email):
        response = self._post_webhook("1500.00")

        self.assertEqual(response.status_code, 200)
        self.funding.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.funding.amount_received, Decimal("1500.00"))
        self.assertEqual(self.payment.status, "réussi")

    def test_signed_webhook_rejects_mismatched_amount(self):
        response = self._post_webhook("999.00")

        self.assertEqual(response.status_code, 400)
        self.funding.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.funding.amount_received, Decimal("0.00"))
        self.assertEqual(self.payment.status, "en_attente")

    def test_signed_webhook_rejects_missing_amount(self):
        response = self._post_webhook(None)

        self.assertEqual(response.status_code, 400)
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.amount_received, Decimal("0.00"))


class ReconcilePendingPaymentsTests(TestCase):
    """Point a : réconciliation/expiration des paiements restés en attente."""

    def _stale_donation(self, hours=48):
        donation = Donation.objects.create(
            amount=Decimal("10000"),
            donor_email="donor@example.com",
            transaction_id="tok_reconcile",
            status="en_attente",
        )
        # created_at est auto_now_add : on le force via update() pour simuler l'âge.
        Donation.objects.filter(pk=donation.pk).update(
            created_at=timezone.now() - timedelta(hours=hours)
        )
        donation.refresh_from_db()
        return donation

    def test_noop_when_disabled(self):
        donation = self._stale_donation()
        result = reconcile_pending_payments()
        self.assertEqual(result, {"enabled": False})
        donation.refresh_from_db()
        self.assertEqual(donation.status, "en_attente")

    @override_settings(PAYMENT_RECONCILIATION_ENABLED=True, PENDING_PAYMENT_EXPIRY_HOURS=24)
    def test_expires_stale_pending_when_unverifiable(self):
        donation = self._stale_donation(hours=48)
        with patch("page.views._verify_payment_status_with_djomy", return_value=None):
            result = reconcile_pending_payments()
        donation.refresh_from_db()
        self.assertEqual(donation.status, "échoué")
        self.assertEqual(result["expired"], 1)

    @override_settings(PAYMENT_RECONCILIATION_ENABLED=True, PENDING_PAYMENT_EXPIRY_HOURS=24)
    def test_confirms_when_provider_reports_success(self):
        donation = self._stale_donation(hours=48)
        with patch("page.views._verify_payment_status_with_djomy", return_value="réussi"):
            result = reconcile_pending_payments()
        donation.refresh_from_db()
        self.assertNotIn(donation.status, ("en_attente", "échoué"))
        self.assertEqual(result["succeeded"], 1)

    @override_settings(PAYMENT_RECONCILIATION_ENABLED=True, PENDING_PAYMENT_EXPIRY_HOURS=24)
    def test_recent_pending_is_left_untouched(self):
        donation = self._stale_donation(hours=1)  # plus récent que le délai
        with patch("page.views._verify_payment_status_with_djomy", return_value=None):
            result = reconcile_pending_payments()
        donation.refresh_from_db()
        self.assertEqual(donation.status, "en_attente")
        self.assertEqual(result["checked"], 0)


class CommentEndpointTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="user1", password="pass1234")
        self.funding = FundingRequest.objects.create(
            beneficiary_name="Test Beneficiary",
            funding_amount=Decimal("1000.00"),
            description_needs="Need support",
            principal_image="img/Fundings/test.png",
            amount_received=Decimal("0.00"),
        )
        self.alert = LossAlert.objects.create(
            name="Test Alert",
            description="Need help",
            principal_image="img/alerts/test.png",
            address="Test Address",
            date_alert="2025-01-01",
        )

    def test_add_comment_requires_authentication(self):
        url = reverse("add_comment", kwargs={"model_name": "fundingrequest", "object_id": self.funding.id})
        response = self.client.post(url, {"text": "Hello"})
        self.assertEqual(response.status_code, 302)

    def test_add_comment_rejects_unsupported_model(self):
        self.client.login(username="user1", password="pass1234")
        url = reverse("add_comment", kwargs={"model_name": "unknownmodel", "object_id": self.funding.id})
        response = self.client.post(url, {"text": "Hello"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Comment.objects.count(), 0)

    def test_add_comment_creates_comment_for_allowed_model(self):
        self.client.login(username="user1", password="pass1234")
        url = reverse("add_comment", kwargs={"model_name": "fundingrequest", "object_id": self.funding.id})
        response = self.client.post(url, {"text": "Commentaire test"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertIn("comment_html", payload)

    def test_add_comment_works_for_loss_alert(self):
        self.client.login(username="user1", password="pass1234")
        url = reverse("add_comment", kwargs={"model_name": "lossalert", "object_id": self.alert.id})
        response = self.client.post(url, {"text": "Commentaire alerte"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertIn("comment_html", payload)

    def test_edit_comment_updates_text(self):
        self.client.login(username="user1", password="pass1234")
        comment = Comment.objects.create(
            user=self.user,
            content_object=self.funding,
            text="Texte initial",
        )
        url = reverse("js_edit_comment", kwargs={"comment_id": comment.id})
        response = self.client.post(url, data='{"text":"Texte modifie"}', content_type="application/json")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        comment.refresh_from_db()
        self.assertEqual(comment.text, "Texte modifie")

    def test_delete_comment_removes_comment(self):
        self.client.login(username="user1", password="pass1234")
        comment = Comment.objects.create(
            user=self.user,
            content_object=self.funding,
            text="Texte a supprimer",
        )
        url = reverse("js_delete_comment", kwargs={"comment_id": comment.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())
