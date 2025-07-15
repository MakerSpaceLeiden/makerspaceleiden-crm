import json

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from acl.models import Machine
from members.models import User


class MembersApiTests(TestCase):
    def test_members_list_returns_403(self):
        client = APIClient()
        response = client.get("/api/v1/members/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_members_list_returns_200_for_authed(self):
        user_password = "testpassword"
        user = User.objects.create_user(
            email="testuser@example.com",
            password=user_password,
            first_name="Test",
            last_name="User",
            telegram_user_id="123456789",
        )
        client = APIClient()
        self.assertIs(client.login(email=user.email, password=user_password), True)
        response = client.get("/api/v1/members/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content)["data"],
            [
                {
                    "id": user.id,
                    "url": "https://mijn.makerspaceleiden.nl/acl/member/"
                    + str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "image": None,
                }
            ],
        )


class MachinesApiTests(TestCase):
    def test_machines_list_returns_403(self):
        client = APIClient()
        response = client.get("/api/v1/machines/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_machines_list_returns_200_for_authed(self):
        user_password = "testpassword"
        user = User.objects.create_user(
            email="testuser@example.com",
            password=user_password,
            first_name="Test",
            last_name="User",
            telegram_user_id="123456789",
        )

        machine = Machine.objects.create(name="Test Machine")
        client = APIClient()
        self.assertIs(client.login(email=user.email, password=user_password), True)
        response = client.get("/api/v1/machines/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            json.loads(response.content)["data"][-1],
            {
                "id": machine.id,
                "description": machine.description,
                "name": machine.name,
                "out_of_order": machine.out_of_order,
                "category": machine.category,
                "location": None,
                "logs": [],
                "last_updated": None,
            },
        )
