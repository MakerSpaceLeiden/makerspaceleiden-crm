import json
import os
from unittest import TestCase

import jsonschema
from django.apps import apps
from django.test import Client

from selfservice.test_helpers.mocks import MockAggregatorAdapter


# Load the schema from a file
def load_schema(schema_path):
    with open(schema_path, "r") as schema_file:
        return json.load(schema_file)


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

        schema = load_schema(
            os.path.join(os.path.dirname(__file__), "./fixtures/spaceapi-schema.json")
        )

        jsonschema.validate(json.loads(response.content), schema)
