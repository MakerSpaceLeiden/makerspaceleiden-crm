import os
import tempfile
from http import HTTPStatus

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner
from django.test import Client, TestCase, override_settings
from django.test.client import RequestFactory

from makerspaceleiden.utils import derive_initials

User = get_user_model()


def generate_signed_url(req):
    signer = TimestampSigner()
    signed_val = signer.sign(req.path)
    return req.build_absolute_uri(signed_val)


class MakerspaceleidenTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(
            "Intranet – " + settings.SITE_NAME, response.content.decode("utf-8")
        )

    @pytest.mark.django_db
    def test_login(self):
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(
            "<title>Login – " + settings.SITE_NAME + "</title>",
            response.content.decode("utf-8"),
        )


class DeriveInitialsTest(TestCase):
    def test_derive_initials_cases(self):
        cases = [
            (("Abd", "al-Ghazali"), "AG"),
            (("Abd", "Al-Ghazali"), "AG"),
            (("Abd", "al Ghazali"), "AG"),
            (("Sara", "el-Ghazali"), "SG"),
            (("Sara", "El Ghazali"), "SG"),
            (("John", "Doe"), "JD"),
            (("Anna", "Smith"), "AS"),
            (("Jan", "van de Smith"), "JS"),
            (("Piet", "Van Vliet"), "PV"),
            (("Kees", "de Groot"), "KG"),
            (("Sanne", "van der Meer"), "SM"),
            (("Lotte", "ten Brink"), "LB"),
            (("Cher", ""), "C"),
            (("", "Madonna"), "M"),
            (("Hy-Phenated", "Name"), "HN"),
        ]
        for (first, last), expected in cases:
            with self.subTest(first_name=first, last_name=last):
                self.assertEqual(derive_initials(first, last), expected)


class ProtectedMediaViewTest(TestCase):
    """Tests for the protected_media view with minimal abstraction"""

    def setUp(self):
        self.client = Client()
        self._create_users()
        self._create_test_files()

    # def tearDown(self):
    #     self._cleanup_files()

    def _create_users(self):
        """Create test users with different permission levels"""
        self.regular_user = User.objects.create_user(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            password="testpassword123",
            telegram_user_id="123456789",
        )

        self.superuser = User.objects.create_superuser(
            email="superuser@example.com",
            first_name="Super",
            last_name="User",
            password="superpassword123",
            telegram_user_id="987654321",
        )

        self.staff_user = User.objects.create_user(
            email="staff@example.com",
            first_name="Staff",
            last_name="User",
            password="staffpassword123",
            telegram_user_id="555666777",
            is_staff=True,
        )

    def _create_test_files(self):
        """Create temporary test files"""
        self.temp_media_dir = tempfile.mkdtemp()
        self.test_content = "Test file content for protected media"
        self.nested_content = "Nested test file content"

        # Main test file
        self.test_file_path = os.path.join(self.temp_media_dir, "test_file.txt")
        with open(self.test_file_path, "w") as f:
            f.write(self.test_content)

        # Nested file in subdirectory
        self.subdir = os.path.join(self.temp_media_dir, "subdirectory")
        os.makedirs(self.subdir, exist_ok=True)
        self.nested_file_path = os.path.join(self.subdir, "nested_file.pdf")
        with open(self.nested_file_path, "w") as f:
            f.write(self.nested_content)

    def _cleanup_files(self):
        """Clean up temporary files"""
        for path in [self.test_file_path, self.nested_file_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.subdir):
            os.rmdir(self.subdir)
        if os.path.exists(self.temp_media_dir):
            os.rmdir(self.temp_media_dir)

    def _get_file_content(self, response):
        """Helper to get content from FileResponse"""
        return b"".join(response.streaming_content).decode()

    # Authentication Tests
    def test_unauthenticated_user_denied(self):
        """Unauthenticated users should get 403"""
        with override_settings(MEDIA_ROOT=self.temp_media_dir, MEDIA_URL="/media/"):
            response = self.client.get("/media/test_file.txt")

            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
            self.assertEqual(response.content.decode(), "XS denied")
            self.assertEqual(response["Content-Type"], "text/plain")

    def test_authenticated_users_allowed(self):
        """All authenticated user types should be able to access files"""
        users = [
            (self.regular_user, "regular user"),
            (self.superuser, "superuser"),
            (self.staff_user, "staff user"),
        ]

        with override_settings(MEDIA_ROOT=self.temp_media_dir, MEDIA_URL="/media/"):
            for user, description in users:
                with self.subTest(user_type=description):
                    if user == self.regular_user:
                        self.client.login(email=user.email, password="testpassword123")
                    elif user == self.superuser:
                        self.client.login(email=user.email, password="superpassword123")
                    elif user == self.staff_user:
                        self.client.login(email=user.email, password="staffpassword123")

                    response = self.client.get("/media/test_file.txt")

                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertEqual(
                        self._get_file_content(response), self.test_content
                    )

    # Signed URL Tests
    def test_signed_url(self):
        """Signed URL should work"""
        with override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            MEDIA_URL="/media/",
        ):
            url = "/media/test_file.txt"

            factory = RequestFactory()
            req = factory.get(url)
            signed_url = generate_signed_url(req)

            response = self.client.get(signed_url)

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(self._get_file_content(response), self.test_content)

    # Bearer Token Tests
    def test_bearer_token_x_header(self):
        """X-Bearer header should work"""
        with override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            MEDIA_URL="/media/",
            UT_BEARER_SECRET="test_secret",
        ):
            response = self.client.get(
                "/media/test_file.txt", HTTP_X_BEARER="test_secret"
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(self._get_file_content(response), self.test_content)

    def test_bearer_token_authorization_header(self):
        """Authorization: Bearer header should work"""
        with override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            MEDIA_URL="/media/",
            UT_BEARER_SECRET="test_secret",
        ):
            response = self.client.get(
                "/media/test_file.txt", HTTP_AUTHORIZATION="Bearer test_secret"
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(self._get_file_content(response), self.test_content)

    def test_multiple_bearer_secrets(self):
        """Multiple space-separated bearer secrets should all work"""
        with override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            MEDIA_URL="/media/",
            UT_BEARER_SECRET="secret1 secret2 secret3",
        ):
            for secret in ["secret1", "secret2", "secret3"]:
                with self.subTest(secret=secret):
                    response = self.client.get(
                        "/media/test_file.txt", HTTP_X_BEARER=secret
                    )

                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertEqual(
                        self._get_file_content(response), self.test_content
                    )

    def test_invalid_bearer_tokens_denied(self):
        """Invalid bearer tokens should be denied"""
        test_cases = [
            ("invalid_secret", {"HTTP_X_BEARER": "invalid_secret"}),
            ("Basic auth", {"HTTP_AUTHORIZATION": "Basic dXNlcjpwYXNz"}),
            ("Empty bearer", {"HTTP_AUTHORIZATION": "Bearer"}),
            ("Bearer with space", {"HTTP_AUTHORIZATION": "Bearer "}),
            ("Wrong format", {"HTTP_AUTHORIZATION": "InvalidFormat token"}),
        ]

        with override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            MEDIA_URL="/media/",
            UT_BEARER_SECRET="valid_secret",
        ):
            for description, headers in test_cases:
                with self.subTest(case=description):
                    response = self.client.get("/media/test_file.txt", **headers)

                    self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
                    self.assertEqual(response.content.decode(), "XS denied")

    def test_case_insensitive_bearer_header(self):
        """Bearer header should be case insensitive"""
        cases = ["Bearer", "bearer", "BEARER", "BeArEr"]

        with override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            MEDIA_URL="/media/",
            UT_BEARER_SECRET="valid_secret",
        ):
            for case in cases:
                with self.subTest(case=case):
                    response = self.client.get(
                        "/media/test_file.txt",
                        HTTP_AUTHORIZATION=f"{case} valid_secret",
                    )

                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertEqual(
                        self._get_file_content(response), self.test_content
                    )

    # File Serving Tests
    def test_nested_file_paths(self):
        """Should serve files from subdirectories"""
        with override_settings(MEDIA_ROOT=self.temp_media_dir, MEDIA_URL="/media/"):
            self.client.login(email=self.regular_user.email, password="testpassword123")

            response = self.client.get("/media/subdirectory/nested_file.pdf")

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(self._get_file_content(response), self.nested_content)

    def test_nonexistent_file_404(self):
        """Non-existent files should return 404"""
        with override_settings(MEDIA_ROOT=self.temp_media_dir, MEDIA_URL="/media/"):
            self.client.login(email=self.regular_user.email, password="testpassword123")

            response = self.client.get("/media/nonexistent.txt")

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_bearer_token_with_missing_file(self):
        """Bearer token should work but still return 404 for missing files"""
        with override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            MEDIA_URL="/media/",
            UT_BEARER_SECRET="test_secret",
        ):
            response = self.client.get(
                "/media/missing.txt", HTTP_X_BEARER="test_secret"
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_directory_traversal_protection(self):
        """Directory traversal attempts should be blocked"""
        attempts = [
            "../../../etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "....//....//etc/passwd",
        ]

        with override_settings(MEDIA_ROOT=self.temp_media_dir, MEDIA_URL="/media/"):
            self.client.login(email=self.regular_user.email, password="testpassword123")

            for attempt in attempts:
                with self.subTest(attempt=attempt):
                    response = self.client.get(f"/media/{attempt}")

                    # Should not return 200 - either 404, 403, or 400
                    self.assertIn(
                        response.status_code,
                        [
                            HTTPStatus.NOT_FOUND,
                            HTTPStatus.FORBIDDEN,
                            HTTPStatus.BAD_REQUEST,
                        ],
                    )
