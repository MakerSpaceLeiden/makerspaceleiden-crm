# Create your tests here.
from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from acl.models import Entitlement, Machine, PermitType
from members.models import User


class AclTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Create common test data
        self.admin = User.objects.create_superuser(
            email="admin@test.nl", password="testpassword", is_superuser=True
        )
        woodpermit, wasCreated = PermitType.objects.get_or_create(
            name="Wood Instruction", description="Can issue wood machine entitlement"
        )
        self.assertTrue(wasCreated)
        self.woodpermit = woodpermit

        self.machine = Machine.objects.create(
            name="First machine",
            node_name="Node1",
            description="Test",
            requires_instruction=True,
            requires_permit=self.woodpermit,
        )

    # Verify that a user with no permisssions can not
    # add instructions for a machine they are not entitled for.
    def test_record_instructions_no_permissions(self):
        testUser = User.objects.create_user(
            email="test@test.nl", password="testpassword"
        )

        success = self.client.login(email=testUser.email, password="testpassword")
        self.assertTrue(success)

        response = self.client.get(reverse("add_instruction"))
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            "Sorry - you have not had instructions on any machine yourself",
            response.content.decode("utf-8"),
        )

    # Verify that a user with necessary permissions
    # can add instructions for a machine they are entitled for.
    def test_record_instructions_with_permissions(self):
        testUser = User.objects.create_user(
            email="test@test.nl", password="testpassword"
        )
        testUser.save()

        Entitlement.objects.create(
            active=True, permit=self.woodpermit, holder=testUser, issuer=self.admin
        )

        success = self.client.login(email=testUser.email, password="testpassword")
        self.assertTrue(success)

        response = self.client.get(reverse("add_instruction"))
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            self.machine.name,
            response.content.decode("utf-8"),
        )
        self.assertNotIn(
            "Sorry - you have not had instructions on any machine yourself",
            response.content.decode("utf-8"),
        )

    # Verify that a super user can add instructions
    # for a machine they are entitled for.
    def test_record_instructions_admin_user(self):
        success = self.client.login(email=self.admin.email, password="testpassword")
        self.assertTrue(success)

        response = self.client.get(reverse("add_instruction"))
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            self.machine.name,
            response.content.decode("utf-8"),
        )
        self.assertNotIn(
            "Sorry - you have not had instructions on any machine yourself",
            response.content.decode("utf-8"),
        )

    def test_space_state_get(self):
        user = User.objects.create_user(
            email="test@test.nl",
            password="testpassword",
            first_name="Test",
            last_name="User",
            is_onsite=True,
        )

        success = self.client.login(email=self.admin.email, password="testpassword")
        self.assertTrue(success)

        response = self.client.get(reverse("space_state"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        html = response.content.decode("utf-8")
        self.assertIn("State of the Space", html)
        self.assertIn(user.name(), html)
        self.assertNotIn('data-test-hook="member-checkout"', html)

    def test_space_state_get_self(self):
        user = User.objects.create_user(
            email="test@test.nl",
            password="testpassword",
            first_name="Test",
            last_name="User",
            is_onsite=True,
        )

        success = self.client.login(email=user.email, password="testpassword")
        self.assertTrue(success)

        response = self.client.get(reverse("space_state"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        html = response.content.decode("utf-8")
        self.assertIn("State of the Space", html)
        self.assertIn(user.name(), html)
        self.assertIn('data-test-hook="member-checkout"', html)

    def test_space_state_checkout(self):
        user = User.objects.create_user(
            email="test@test.nl",
            password="testpassword",
            first_name="Test",
            last_name="User",
            is_onsite=True,
        )

        success = self.client.login(email=user.email, password="testpassword")
        self.assertTrue(success)

        response = self.client.post(reverse("checkout_from_space_post"), follow=True)

        user.refresh_from_db()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(user.is_onsite, "user is checked out")
        self.assertIn("You are now checked out.", response.content.decode("utf-8"))
