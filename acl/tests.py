import pytest

from members.models import User

from .models import Machine, NodeCapability, PermitType, RecentUse


@pytest.mark.django_db
class TestRecentUse:
    @pytest.fixture(autouse=True)
    def setup(self, db):
        self.user = User.objects.create_user(
            first_name="Model",
            last_name="Test",
            password="testpassword",
            email="modeltest@example.com",
        )

        self.permit = PermitType.objects.create(
            name="Wood Instruction",
            description="Can issue wood machine entitlement",
            require_ok_trustee=False,
        )

    def test_recentuse_create(self):
        machine = Machine.objects.create(
            name="First machine",
            node_name="Node1",
            description="Test",
            requires_instruction=True,
            requires_permit=self.permit,
        )

        RecentUse.objects.create(user=self.user, machine=machine)

        assert RecentUse.objects.count() == 1
        self.user.refresh_from_db()
        assert not self.user.is_onsite

    def test_recentuse_create_with_login(self):
        machine = Machine.objects.create(
            name="First machine",
            node_name="Node1",
            description="Test",
            requires_instruction=True,
            requires_permit=self.permit,
            node_capability=NodeCapability.LOGIN,
        )

        RecentUse.objects.create(user=self.user, machine=machine)

        assert RecentUse.objects.count() == 1
        self.user.refresh_from_db()
        assert self.user.is_onsite

    def test_recentuse_create_with_logout(self):
        self.user.checkin(location=None)

        machine = Machine.objects.create(
            name="First machine",
            node_name="Node1",
            description="Test",
            requires_instruction=True,
            requires_permit=self.permit,
            node_capability=NodeCapability.LOGOUT,
        )

        RecentUse.objects.create(user=self.user, machine=machine)

        assert RecentUse.objects.count() == 1
        self.user.refresh_from_db()
        assert not self.user.is_onsite
