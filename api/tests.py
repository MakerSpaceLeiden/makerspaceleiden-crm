import json
from datetime import date, time

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from acl.models import Machine
from agenda.models import Agenda
from members.models import User


class EventsApiTests(TestCase):
    def test_events_list_returns_403(self):
        client = APIClient()
        response = client.get("/api/v1/events/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_events_list_returns_200_for_authed(self):
        user_password = "testpassword"
        user = User.objects.create_user(
            email="testuser@example.com",
            password=user_password,
            first_name="Test",
            last_name="User",
            telegram_user_id="123456789",
        )
        event = Agenda.objects.create(
            startdate=date.today(),
            starttime=time(9, 0),
            enddate=date.today(),
            endtime=time(10, 0),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=user,
        )
        client = APIClient()
        self.assertIs(client.login(email=user.email, password=user_password), True)
        response = client.get("/api/v1/events/")
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            json_response["meta"],
            {
                "total": 1,
            },
        )
        self.assertDictEqual(
            json_response["data"][-1],
            {
                "id": event.id,
                "name": event.item_title,
                "description": event.item_details,
                "start_datetime": event.start_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                "end_datetime": event.end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
            },
        )


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
        json_response = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            json_response["meta"],
            {
                "total": 1,
            },
        )
        self.assertEqual(
            json_response["data"],
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
    def setUp(self):
        self.user_password = "testpassword"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password=self.user_password,
            first_name="Test",
            last_name="User",
            telegram_user_id="123456789",
        )

    def test_machines_list_returns_403(self):
        client = APIClient()
        response = client.get("/api/v1/machines/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_machines_list_returns_200_for_authed(self):
        machine = Machine.objects.create(name="Test Machine")
        client = APIClient()
        self.assertTrue(
            client.login(email=self.user.email, password=self.user_password)
        )

        response = client.get("/api/v1/machines/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_response = json.loads(response.content)
        self.assertDictEqual(
            json_response["meta"],
            {
                "total": 1,
            },
        )
        self.assertDictEqual(
            json_response["data"][-1],
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

    def test_machines_list_post_filter_out_of_order_true(self):
        # Create two machines, one out_of_order, one not
        machine_ok = Machine.objects.create(name="OK Machine", out_of_order=False)
        machine_ooo = Machine.objects.create(name="Broken Machine", out_of_order=True)

        client = APIClient()
        self.assertTrue(
            client.login(email=self.user.email, password=self.user_password)
        )

        response = client.get("/api/v1/machines/?out_of_order=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)["data"]
        # Only the out_of_order machine should be present
        self.assertTrue(any(m["id"] == machine_ooo.id for m in data))
        self.assertFalse(any(m["id"] == machine_ok.id for m in data))
        for m in data:
            self.assertTrue(m["out_of_order"])

    def test_machines_list_post_filter_out_of_order_false(self):
        # Create two machines, one out_of_order, one not
        machine_ok = Machine.objects.create(name="OK Machine", out_of_order=False)
        machine_ooo = Machine.objects.create(name="Broken Machine", out_of_order=True)

        client = APIClient()
        self.assertTrue(
            client.login(email=self.user.email, password=self.user_password)
        )

        response = client.get("/api/v1/machines/?out_of_order=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)["data"]
        # Only the not out_of_order machine should be present
        self.assertTrue(any(m["id"] == machine_ok.id for m in data))
        self.assertFalse(any(m["id"] == machine_ooo.id for m in data))
        for m in data:
            self.assertFalse(m["out_of_order"])
