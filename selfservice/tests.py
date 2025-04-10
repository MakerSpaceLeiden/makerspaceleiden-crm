# Create your tests here.
from django.test import Client, TestCase
from django.urls import reverse

from acl.models import Machine, PermitType
from members.models import User


class AclTest(TestCase):
    def setUp(self):
        User.objects.create_user(email="test@test.nl", password="testpassword")
        self.client = Client()

    def test_record_instructions_no_permissions(self):
        woodpermit, wasCreated = PermitType.objects.get_or_create(
            name="Wood Instruction", description="Can issue wood machine entitlement"
        )
        self.assertTrue(wasCreated)

        Machine.objects.create(
            name="First machine",
            node_name="Node1",
            description="Test",
            requires_instruction=True,
            requires_permit=woodpermit,
        )

        success = self.client.login(email="test@test.nl", password="testpassword")
        self.assertTrue(success)

        response = self.client.get(reverse("add_instruction"))
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "Sorry - you have not had instructions on any machine yourself",
            response.content.decode("utf-8"),
        )

    def test_record_instructions_with_permissions(self):
        woodpermit, wasCreated = PermitType.objects.get_or_create(
            name="Wood Instruction", description="Can issue wood machine entitlement"
        )
        self.assertTrue(wasCreated)

        Machine.objects.create(
            name="First machine",
            node_name="Node1",
            description="Test",
            requires_instruction=True,
            requires_permit=woodpermit,
        )

        User.objects.create_superuser(
            email="admin@test.nl", password="testpassword", is_superuser=True
        )

        success = self.client.login(
            email="admin@test.nl",
            password="testpassword",
        )
        self.assertTrue(success)

        response = self.client.get(reverse("add_instruction"))
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "First machine",
            response.content.decode("utf-8"),
        )
        self.assertNotIn(
            "Sorry - you have not had instructions on any machine yourself",
            response.content.decode("utf-8"),
        )
