import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from page.models import UserDetails

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="sosguinee-test-media-")


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
