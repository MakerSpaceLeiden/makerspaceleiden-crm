from http import HTTPStatus
from unittest import TestCase

import pytest
from django.conf import settings
from django.test import Client, override_settings

from makerspaceleiden.utils import derive_initials


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

    def test_oauth2_openid_configuration_available(self):
        with override_settings(
            OAUTH2_PROVIDER={
                "OIDC_ENABLED": True,
            }
        ):
            response = self.client.get("/oauth2/.well-known/openid-configuration")
            self.assertEqual(response.status_code, HTTPStatus.OK)


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
