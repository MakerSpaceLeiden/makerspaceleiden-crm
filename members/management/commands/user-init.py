import logging
import secrets

from django.conf import settings
from django.core.management.base import BaseCommand

from members.models import User

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Creates some role/users with special functions. Part of the general setup"

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(email="admin@admin.nl")
        except Exception:
            logger.warning("Admin user not found, creating")
            admin = User.objects.create_superuser("admin@admin.nl", "1234")
            admin.first_name = ("Ad",)
            admin.last_name = "Min"
            admin.save()

        try:
            none_user = User.objects.get(email="none")
        except Exception:
            logger.warning("No none/aggregate user was found. Creating.")
            none_user = User.objects.create_superuser("none", secrets.token_urlsafe(32))
            none_user.first_name = "Former"
            none_user.last_name = "Participant(s)"
            none_user.is_active = False
            none_user.save()
            none_user = User.objects.get(email="none")

        if none_user.id != settings.NONE_ID:
            raise Exception(
                f"None user has ID {none_user.id}; while settings specifies {settings.NONE_ID}, please correct."
            )

        try:
            pot_user = User.objects.get(email="jar")
        except Exception:
            logger.warning("No kitty/jar was found. Creating.")
            pot_user = User.objects.create_superuser("jar", secrets.token_urlsafe(32))
            pot_user.first_name = "Kitty"
            pot_user.last_name = "Shared jar of money"
            pot_user.is_active = False
            pot_user.save()
            pot_user = User.objects.get(email="jar")

        if pot_user.id != settings.POT_ID:
            raise Exception(
                f"Jar/Pot user has ID {pot_user.id}; while settings specifies {settings.POT_ID}, please correct."
            )
