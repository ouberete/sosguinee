from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from page.models import Comment, Donation, FundPayment, FundingRequest, LossAlert


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
