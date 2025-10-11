from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand

from ...models import Agenda


class Command(BaseCommand):
    help = "Generate recurring events for agenda"

    def handle(self, *args, **options):
        agenda_items = Agenda.objects.all().filter(recurrences__isnull=False)
        created = []
        start = datetime.now(tz=timezone.utc)
        end = datetime.now(tz=timezone.utc) + timedelta(days=31)

        for item in agenda_items:
            created += Agenda.objects.generate_occurrences(item, start, end)

        self.stdout.write(
            self.style.SUCCESS(f"Generated {len(created)} recurring events")
        )
