from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from django.conf import settings

from members.models import User


class Command(BaseCommand):
    help = "Add users for demo to petty cash group"

    def handle(self, *args, **options):
        grp, created = Group.objects.get_or_create(name=settings.PETTYCASH_ADMIN_GROUP)

        for user in User.objects.all():
            user.groups.add(grp)
            user._change_reason = "Auto add all users to settings.PETTYCASH_ADMIN_GROUP"
            user.save()
