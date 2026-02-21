from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from page.models import Comment, Donation, FundPayment, FundingRequest


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
        url = reverse("paycard_payment_callback", kwargs={"payment_id": donation.id, "type": "Don"})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        donation.refresh_from_db()
        self.assertEqual(donation.status, "en_attente")

    def test_donation_callback_accepts_valid_token(self):
        donation = Donation.objects.create(
            amount=Decimal("10000"),
            donor_email="donor@example.com",
            transaction_id="tok_valid",
        )
        url = reverse("paycard_payment_callback", kwargs={"payment_id": donation.id, "type": "Don"})

        response = self.client.get(f"{url}?token={donation.transaction_id}")
        self.assertEqual(response.status_code, 200)
        donation.refresh_from_db()
        self.assertNotEqual(donation.status, "en_attente")

    def test_funding_callback_updates_received_amount_once(self):
        funding = self._funding()
        payment = FundPayment.objects.create(
            funding_request=funding,
            amount=Decimal("150.00"),
            donor_email="donor@example.com",
            transaction_id="tok_funding",
        )
        url = reverse("paycard_payment_callback", kwargs={"payment_id": payment.id, "type": "Financement"})

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
