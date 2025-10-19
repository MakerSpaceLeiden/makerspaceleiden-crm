from django.core.management.base import BaseCommand
from datetime import timedelta, datetime
from django.utils import timezone
from members.models import User

MAX_HOURS_BEFORE_STALE = 8

class Command(BaseCommand):
    help = "Automated checkout of members"

    def handle(self, *args, **options):
        """Checkouts members who have been checked in for more than configured maximum hours"""
        checked_in = User.objects.filter(is_onsite=True, onsite_updated_at__lte  = datetime.now(timezone.utc) - timedelta(hours=MAX_HOURS_BEFORE_STALE))
        for u in checked_in:
            u.checkout() 
