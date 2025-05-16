from unittest import TestCase

from django.apps import apps
from django.test import Client

from selfservice.tests.mocks import MockAggregatorAdapter


class SpaceApiTest(TestCase):
    apps.get_app_config("selfservice").aggregator_adapter = MockAggregatorAdapter()

    def setUp(self):
        self.client = Client()

    def test_redirect(self):
        response = self.client.get("/spaceapi/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/spaceapi/0.13")

    def test_basic(self):
        response = self.client.get("/spaceapi/0.13")
        self.assertEqual(response.status_code, 200)
