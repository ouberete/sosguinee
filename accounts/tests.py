import shutil
import tempfile
from unittest.mock import MagicMock, call, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserSubscription
from ensemble224.utils.custom_email_backend import CustomEmailBackend
from page.models import UserDetails
from accounts.forms import ProfileForm, UserDocumentForm, UserInfosForm
from accounts.tasks import cleanup_expired_subscriptions, send_subscription_reminders

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="ensemble224-test-media-")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProtectedUserDocumentTests(TestCase):
    """
    Les documents personnels (media/user_images/...) ne doivent être servis
    qu'au propriétaire du profil ou au staff — jamais publiquement.
    """

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username="owner", password="pass1234")
        self.other = User.objects.create_user(username="other", password="pass1234")
        self.staff = User.objects.create_user(
            username="staff", password="pass1234", is_staff=True
        )
        self.details = UserDetails.objects.create(
            user=self.owner,
            id_card=SimpleUploadedFile("carte.pdf", b"%PDF-1.4 contenu confidentiel"),
        )
        self.url = reverse(
            "protected_user_document",
            kwargs={"path": self.details.id_card.name.replace("user_images/", "", 1)},
        )

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response["Location"])

    def test_other_user_gets_404(self):
        self.client.login(username="other", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_owner_can_download_own_document(self):
        self.client.login(username="owner", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content)[:8], b"%PDF-1.4")

    def test_staff_can_view_any_document(self):
        self.client.login(username="staff", password="pass1234")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_unknown_path_gets_404_for_authenticated_user(self):
        self.client.login(username="owner", password="pass1234")
        response = self.client.get(
            reverse("protected_user_document", kwargs={"path": "id_cards/inexistant.pdf"})
        )
        self.assertEqual(response.status_code, 404)


class ProfileFormTests(TestCase):
    ESSENTIAL_FIELDS = {
        "civility", "first_name", "last_name", "birth_date", "birth_city",
        "nationality", "actual_city", "zip_code", "address", "phone",
        "region", "prefecture", "commune", "quarter",
    }

    def test_update_wizard_keeps_only_essential_information(self):
        self.assertEqual(set(UserInfosForm.base_fields), self.ESSENTIAL_FIELDS)
        self.assertEqual(set(UserInfosForm.Meta.fields), self.ESSENTIAL_FIELDS)

    def test_profile_form_does_not_expose_secondary_fields(self):
        self.assertNotIn("facebook", ProfileForm.base_fields)
        self.assertNotIn("profession", ProfileForm.base_fields)
        self.assertNotIn("user_category", ProfileForm.base_fields)
        self.assertNotIn("bio", ProfileForm.base_fields)

    def test_document_country_is_cleared_without_document(self):
        form = UserDocumentForm(
            data={"id_card_country": "GN", "birth_piece_country": "FR"}
        )
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["id_card_country"])
        self.assertIsNone(form.cleaned_data["birth_piece_country"])

    def test_documents_and_countries_are_optional(self):
        form = UserDocumentForm(data={})
        self.assertTrue(form.is_valid())
        self.assertFalse(form.fields["id_card_country"].required)
        self.assertFalse(form.fields["birth_piece_country"].required)

    def test_valid_pdf_document_is_accepted(self):
        form = UserDocumentForm(
            data={},
            files={"id_card": SimpleUploadedFile("identity.pdf", b"%PDF-1.4 document")},
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_document_with_disallowed_extension_is_rejected(self):
        form = UserDocumentForm(
            data={},
            files={"id_card": SimpleUploadedFile("identity.exe", b"MZ executable")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("id_card", form.errors)

    def test_pdf_extension_with_non_pdf_content_is_rejected(self):
        form = UserDocumentForm(
            data={},
            files={"id_card": SimpleUploadedFile("identity.pdf", b"not a pdf")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("id_card", form.errors)

    def test_oversized_private_document_is_rejected(self):
        from accounts.forms import MAX_PRIVATE_UPLOAD_SIZE

        form = UserDocumentForm(
            data={},
            files={
                "id_card": SimpleUploadedFile(
                    "identity.pdf",
                    b"%PDF-" + b"x" * MAX_PRIVATE_UPLOAD_SIZE,
                )
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("id_card", form.errors)

    def test_photo_with_non_image_content_is_rejected(self):
        form = UserDocumentForm(
            data={},
            files={"photo": SimpleUploadedFile("photo.png", b"not an image")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("photo", form.errors)


class SubscriptionTasksTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="subscriber",
            email="subscriber@example.com",
            password="pass1234",
        )

    def test_subscription_reminder_uses_active_subscription(self):
        subscription = UserSubscription.objects.create(
            user=self.user,
            end_date=timezone.now() + timezone.timedelta(days=5),
        )

        with patch("ensemble224.utils.email_service.EmailService.send_subscription_reminder", return_value=1) as send:
            result = send_subscription_reminders()

        subscription.refresh_from_db()
        self.assertEqual(result, {"reminded": 1})
        self.assertTrue(subscription.reminder_sent)
        send.assert_called_once_with(self.user, queue=False)

    def test_cleanup_deactivates_expired_subscriptions(self):
        subscription = UserSubscription.objects.create(
            user=self.user,
            end_date=timezone.now() - timezone.timedelta(days=1),
        )

        result = cleanup_expired_subscriptions()

        subscription.refresh_from_db()
        self.assertEqual(result, {"cleaned": 1})
        self.assertFalse(subscription.is_active)


@override_settings(
    EMAIL_HOST="smtp.gmail.com",
    EMAIL_PORT=587,
    EMAIL_USE_TLS=True,
    EMAIL_USE_SSL=False,
    EMAIL_HOST_USER="",
    EMAIL_HOST_PASSWORD="",
    EMAIL_CLIENT_DOMAIN="localhost",
)
class CustomEmailBackendTests(SimpleTestCase):
    @patch("ensemble224.utils.custom_email_backend.SMTP")
    def test_starttls_is_bracketed_by_ehlo_commands(self, smtp_factory):
        connection = MagicMock()
        smtp_factory.return_value = connection
        backend = CustomEmailBackend()

        self.assertTrue(backend.open())

        self.assertEqual(
            connection.method_calls,
            [
                call.ehlo(),
                call.starttls(context=backend.ssl_context),
                call.ehlo(),
            ],
        )
