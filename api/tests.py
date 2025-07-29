import json
from datetime import date, datetime, time, timezone

import time_machine
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from acl.models import Machine
from agenda.models import Agenda
from members.models import User


class EventsApiTests(TestCase):
    def setUp(self):
        self.password = "testpassword"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password=self.password,
            first_name="Test",
            last_name="User",
            telegram_user_id="123456789",
        )

    def test_events_list_returns_403(self):
        client = APIClient()
        response = client.get("/api/v1/events/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_events_list_returns_200_for_authed(self):
        event = Agenda.objects.create(
            startdate=date.today(),
            starttime=time(9, 0),
            enddate=date.today(),
            endtime=time(10, 0),
            item_title="Fixture Agenda Title",
            item_details="This is a fixture agenda item for testing.",
            user=self.user,
        )
        client = APIClient()
        self.assertIs(client.login(email=self.user.email, password=self.password), True)
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
                "start_datetime": event.start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_datetime": event.end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "type": event.type,
                "status": None,
            },
        )

    def test_events_list_ordering(self):
        # Create two events: one before, one after the filter date
        new_event = Agenda.objects.create(
            startdatetime=datetime(2023, 2, 5, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2023, 2, 5, 10, 0, tzinfo=timezone.utc),
            item_title="Event 1",
            item_details="First event.",
            user=self.user,
        )
        old_event = Agenda.objects.create(
            startdatetime=datetime(2023, 2, 3, 9, 0, tzinfo=timezone.utc),
            enddatetime=datetime(2023, 2, 3, 10, 0, tzinfo=timezone.utc),
            item_title="Event 2",
            item_details="Second event.",
            user=self.user,
        )
        client = APIClient()
        self.assertTrue(client.login(email=self.user.email, password=self.password))
        response = client.get("/api/v1/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)["data"]
        self.assertEqual(len(data), 2)
        self.assertEqual(old_event.item_title, data[0]["name"])
        self.assertEqual(new_event.item_title, data[1]["name"])

    def test_events_list_filter_start_datetime(self):
        # Create two events: one before, one after the filter date
        event1 = Agenda.objects.create(
            startdate=date(2023, 1, 1),
            starttime=time(9, 0),
            enddate=date(2023, 1, 1),
            endtime=time(10, 0),
            item_title="Event 1",
            item_details="First event.",
            user=self.user,
        )
        event2 = Agenda.objects.create(
            startdate=date(2023, 2, 1),
            starttime=time(9, 0),
            enddate=date(2023, 2, 1),
            endtime=time(10, 0),
            item_title="Event 2",
            item_details="Second event.",
            user=self.user,
        )
        client = APIClient()
        self.assertTrue(client.login(email=self.user.email, password=self.password))
        # Filter for events starting after 2023-01-15
        response = client.get("/api/v1/events/?start_datetime=2023-01-15T00:00:00Z")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)["data"]
        self.assertTrue(any(e["id"] == event2.id for e in data))
        self.assertFalse(any(e["id"] == event1.id for e in data))

    def test_events_list_filter_end_datetime(self):
        # Create two events: one before, one after the filter date
        event1 = Agenda.objects.create(
            startdate=date(2023, 1, 1),
            starttime=time(9, 0),
            enddate=date(2023, 1, 1),
            endtime=time(10, 0),
            item_title="Event 1",
            item_details="First event.",
            user=self.user,
        )
        event2 = Agenda.objects.create(
            startdate=date(2023, 2, 1),
            starttime=time(9, 0),
            enddate=date(2023, 2, 1),
            endtime=time(10, 0),
            item_title="Event 2",
            item_details="Second event.",
            user=self.user,
        )
        client = APIClient()
        self.assertTrue(client.login(email=self.user.email, password=self.password))
        # Filter for events ending before 2023-01-15
        response = client.get("/api/v1/events/?end_datetime=2023-01-15T00:00:00Z")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)["data"]
        self.assertTrue(any(e["id"] == event1.id for e in data))
        self.assertFalse(any(e["id"] == event2.id for e in data))

    def test_events_list_filter_start_and_end_datetime(self):
        # Create three events: one before, one in range, one after
        event1 = Agenda.objects.create(
            startdate=date(2023, 1, 1),
            starttime=time(9, 0),
            enddate=date(2023, 1, 1),
            endtime=time(10, 0),
            item_title="Event 1",
            item_details="First event.",
            user=self.user,
        )
        event2 = Agenda.objects.create(
            startdate=date(2023, 2, 1),
            starttime=time(9, 0),
            enddate=date(2023, 2, 1),
            endtime=time(10, 0),
            item_title="Event 2",
            item_details="Second event.",
            user=self.user,
        )
        event3 = Agenda.objects.create(
            startdate=date(2023, 3, 1),
            starttime=time(9, 0),
            enddate=date(2023, 3, 1),
            endtime=time(10, 0),
            item_title="Event 3",
            item_details="Third event.",
            user=self.user,
        )
        client = APIClient()
        self.assertTrue(client.login(email=self.user.email, password=self.password))
        # Filter for events between 2023-01-15 and 2023-02-15
        response = client.get(
            "/api/v1/events/?start_datetime=2023-01-15T00:00:00Z&end_datetime=2023-02-15T23:59:59Z"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)["data"]
        self.assertTrue(any(e["id"] == event2.id for e in data))
        self.assertFalse(any(e["id"] == event1.id for e in data))
        self.assertFalse(any(e["id"] == event3.id for e in data))


class MembersApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "testpassword"
        self.user = User.objects.create_user(
            email="testuser.member.api@example.com",
            password=self.password,
            first_name="Test",
            last_name="User",
            telegram_user_id="123456789",
        )
        permission = Permission.objects.get(
            codename="add_user", content_type=ContentType.objects.get_for_model(User)
        )
        self.user.user_permissions.add(permission)

    def test_members_list_returns_403(self):
        client = APIClient()
        response = client.get("/api/v1/members/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_members_list_returns_200_for_authed(self):
        client = APIClient()
        self.assertIs(client.login(email=self.user.email, password=self.password), True)
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
                    "id": self.user.id,
                    "url": "https://mijn.makerspaceleiden.nl/acl/member/"
                    + str(self.user.id),
                    "email": self.user.email,
                    "first_name": self.user.first_name,
                    "last_name": self.user.last_name,
                    "image": "http://testserver/avatar/" + str(self.user.id),
                    "is_onsite": False,
                    "images": {
                        "original": "http://testserver/avatar/" + str(self.user.id),
                        "thumbnail": "http://testserver/avatar/" + str(self.user.id),
                    },
                }
            ],
        )

    def test_member_checkin(self):
        client = APIClient()
        self.assertTrue(client.login(email=self.user.email, password=self.password))

        response = client.post(
            f"/api/v1/members/{self.user.id}/checkin/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertDictEqual(
            json.loads(response.content),
            {
                "meta": {
                    "action": "checkin",
                },
                "data": {
                    "id": self.user.id,
                    "is_onsite": True,
                    "onsite_updated_at": self.user.onsite_updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                },
            },
        )

    @time_machine.travel("2025-05-03 10:00")
    def test_member_checkout(self):
        client = APIClient()
        self.assertTrue(client.login(email=self.user.email, password=self.password))

        response = client.post(
            f"/api/v1/members/{self.user.id}/checkout/",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertDictEqual(
            json.loads(response.content),
            {
                "meta": {
                    "action": "checkout",
                },
                "data": {
                    "id": self.user.id,
                    "is_onsite": False,
                    "onsite_updated_at": self.user.onsite_updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                },
            },
        )


class MachinesApiTests(TestCase):
    def setUp(self):
        self.password = "testpassword"
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password=self.password,
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
        self.assertTrue(client.login(email=self.user.email, password=self.password))

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
        self.assertTrue(client.login(email=self.user.email, password=self.password))

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
        self.assertTrue(client.login(email=self.user.email, password=self.password))

        response = client.get("/api/v1/machines/?out_of_order=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)["data"]
        # Only the not out_of_order machine should be present
        self.assertTrue(any(m["id"] == machine_ok.id for m in data))
        self.assertFalse(any(m["id"] == machine_ooo.id for m in data))
        for m in data:
            self.assertFalse(m["out_of_order"])
