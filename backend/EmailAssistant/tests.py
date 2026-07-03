from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import EmailRequestForm
from .views import EMAIL_DRAFT


class AttachmentUploadTests(TestCase):
    def test_email_request_form_accepts_attachments(self):
        self.assertIn("attachments", EmailRequestForm.base_fields)

        uploaded_file = SimpleUploadedFile(
            "photo.png",
            b"fake-image-data",
            content_type="image/png",
        )
        second_file = SimpleUploadedFile(
            "notes.pdf",
            b"fake-pdf-data",
            content_type="application/pdf",
        )

        form = EmailRequestForm(
            data={
                "receiver_email": "recipient@example.com",
                "topic": "Other",
                "category": "General",
                "tone": "Professional",
                "length": "Medium",
                "premium_level": "Basic",
            },
            files={
                "attachments": [uploaded_file, second_file],
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn("attachments", form.files)
        self.assertEqual(len(form.cleaned_data["attachments"]), 2)

    def test_attachment_survives_preview_to_confirm_flow(self):
        user = self._create_user()
        self.client.force_login(user)

        session = self.client.session
        session[EMAIL_DRAFT] = {
            "subject": "Test Subject",
            "body": "Test body",
            "receiver_email": "recipient@example.com",
            "topic": "Other",
            "category": "General",
            "tone": "Professional",
            "length": "Medium",
            "premium_level": "Basic",
            "attachments": [{"name": "photo.png", "path": "attachments/photo.png"}],
        }
        session.save()

        response = self.client.get(reverse("emailassistant:confirm"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "photo.png")

    def _create_user(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.create_user(
            username="attachuser",
            email="attachuser@example.com",
            password="secret123",
        )
