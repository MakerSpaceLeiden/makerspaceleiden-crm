import io
from datetime import date

import pytest
from django.conf import settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from PIL import Image

from members.models import User
from pettycash.models import PettycashReimbursementRequest


def create_test_image(filename="test_receipt.jpg", size=(1200, 1000), format="JPEG"):
    """Create a test image file"""
    image = Image.new("RGB", size, color="red")
    img_io = io.BytesIO()
    image.save(img_io, format=format, quality=85)
    img_io.seek(0)
    content = img_io.read()
    # Ensure we have actual content
    assert len(content) > 0, "Image content should not be empty"
    return SimpleUploadedFile(
        name=filename,
        content=content,
        content_type=f"image/{format.lower()}",
    )


@pytest.mark.django_db
class TestReimburseFormViewImageAttachments:
    """Tests to verify correct image size variation is used in email attachments"""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Set up test data"""
        self.client = Client()

        # Create a test user
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            telegram_user_id="123456789",
        )

        # Ensure POT user exists
        if not User.objects.filter(id=settings.POT_ID).exists():
            User.objects.create(
                id=settings.POT_ID,
                email="pot@makerspaceleiden.nl",
                first_name="Pot",
                last_name="User",
            )

        # Clear mail outbox before each test
        mail.outbox.clear()

    def test_submit_with_image_uses_variation_filename_in_email(self):
        """Test that email attachment filename indicates a variation is being used (not original)"""
        self.client.login(email=self.user.email, password="testpass123")

        test_image = create_test_image("receipt.jpg", size=(1000, 1000))

        print("LADEBUG: test_image", test_image)
        # Ensure file pointer is at the beginning
        test_image.seek(0)

        response = self.client.post(
            reverse("reimburseform"),
            data={
                "dst": str(self.user.id),
                "description": "Test reimbursement with image",
                "amount_0": "25.00",  # djmoney uses amount_0 for the numeric value
                "amount_1": "EUR",  # djmoney uses amount_1 for the currency
                "date": date.today().strftime("%Y-%m-%d"),
                "viaTheBank": "False",
                "scan": test_image,
            },
        )

        # Should create the reimbursement request with image saved
        # If form validation failed, provide helpful error message
        if PettycashReimbursementRequest.objects.count() == 0:
            error_msg = (
                f"Form submission failed. Response status: {response.status_code}."
            )
            # Try to get form errors from response context
            try:
                if hasattr(response, "context") and "form" in response.context:
                    form = response.context["form"]
                    if form.errors:
                        error_msg += f" Form errors: {form.errors}"
            except Exception:
                pass
            # Check if response contains error messages
            if (
                b"error" in response.content.lower()
                or b"invalid" in response.content.lower()
            ):
                error_msg += f" Response may contain errors. First 1000 chars: {response.content[:1000].decode('utf-8', errors='ignore')}"
            assert False, error_msg

        assert PettycashReimbursementRequest.objects.count() == 1
        request = PettycashReimbursementRequest.objects.first()
        assert request.scan is not None

        # Should send email with image attachment
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert self.user.email in email.to
        assert email.attachments is not None
        assert len(email.attachments) == 1

        # Extract the filenames from the attachments
        filelist = []
        for attachment in email.attachments:
            for part in attachment.walk():
                if part.get_filename() is not None:
                    filelist.append(part.get_filename())

        assert request.scan.name.split("/")[-1] not in filelist
        assert request.scan.large.name.split("/")[-1] in filelist
        assert response.status_code == 200
