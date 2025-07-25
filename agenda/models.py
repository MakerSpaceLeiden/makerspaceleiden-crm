import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from simple_history.models import HistoricalRecords

from chores.models import Chore
from makerspaceleiden.settings import TIME_ZONE
from members.models import User

logger = logging.getLogger(__name__)

CEST = ZoneInfo(TIME_ZONE)  # Handles both CET and CEST


class AgendaQuerySet(models.QuerySet):
    def upcoming_chores(self):
        return self.upcoming(chore__isnull=False)

    def upcoming(self, days=90, limit: int = None, **kwargs):
        today = timezone.now().date()
        end_date = today + timedelta(days=days)
        base_kwargs = kwargs.copy()
        start_q = Q(
            startdatetime__gte=today, startdatetime__lte=end_date, **base_kwargs
        )
        end_q = Q(enddatetime__gte=today, **base_kwargs)
        return self.filter(start_q | end_q).order_by("startdatetime", "item_title")[
            :limit
        ]

    def previous(self, days=90, limit: int = None, **kwargs):
        today = timezone.now().date()
        end_date = today - timedelta(days=days)
        base_kwargs = kwargs.copy()
        start_q = Q(
            startdatetime__lte=today, startdatetime__gte=end_date, **base_kwargs
        )
        end_q = Q(enddatetime__lte=today, **base_kwargs)
        return self.filter(start_q & end_q).order_by("startdatetime", "item_title")[
            :limit
        ]


class Agenda(models.Model):
    startdatetime = models.DateTimeField(null=True)
    enddatetime = models.DateTimeField(null=True)
    item_title = models.TextField(max_length=600, default="")
    item_details = models.TextField(max_length=5000, blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    history = HistoricalRecords()

    # Deprecated – These will be removed in the near future
    startdate = models.DateField(null=True)
    starttime = models.TimeField(null=True)
    enddate = models.DateField(null=True)
    endtime = models.TimeField(null=True)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("overdue", "Overdue"),
        ("help_wanted", "Help Wanted"),
    ]

    chore = models.ForeignKey(Chore, null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=None, null=True
    )

    objects = AgendaQuerySet.as_manager()

    @property
    def start_datetime(self):
        if self.startdatetime:
            return self.startdatetime
        if self.startdate and self.starttime:
            dt = datetime.combine(self.startdate, self.starttime)
            if timezone.is_naive(dt):
                dt = dt.replace(tzinfo=CEST)
            return dt.astimezone(timezone.utc)
        return None

    @property
    def end_datetime(self):
        if self.enddatetime:
            return self.enddatetime
        if self.enddate and self.endtime:
            dt = datetime.combine(self.enddate, self.endtime)
            if timezone.is_naive(dt):
                dt = dt.replace(tzinfo=CEST)
            return dt.astimezone(timezone.utc)
        return None

    @property
    def type(self) -> str:
        if self.chore:
            return "chore"
        return "social"

    @property
    def display_status(self) -> str:
        if self.type != "chore":
            return ""

        if self.is_active and (self.status in ["", "pending"] or self.status is None):
            return "help wanted"

        status = "pending"
        return self.status if self.status else status

    @property
    def display_datetime(self) -> str:
        """
        Returns a string like 'Monday, 10/07 – 17/07' or just the start date if no end date.
        """
        if not self.start_datetime:
            return ""

        start = self.start_datetime.astimezone(CEST)

        start_str = start.strftime("%A, %-d/%-m")
        if self.end_datetime:
            end = self.end_datetime.astimezone(CEST)
            end_str = end.strftime("%-d/%-m")

            if start.strftime("%-d/%-m") == end_str:
                # Return a single day with time duration
                return f"{start_str} {start.strftime('%-H')}–{end.strftime('%-H')}h"

            if start.strftime("%m") == self.end_datetime.strftime("%m"):
                return f"{start.strftime('%A, %-d')}–{end.strftime('%-d/%-m')}"

            return f"{start_str} – {end_str}"
        return start_str

    @property
    def is_active(self) -> bool:
        now = datetime.now(tz=timezone.utc)
        return self.startdatetime <= now and self.enddatetime >= now

    def _get_utc_from_cest_date_and_time(self, date, time):
        if date and time:
            dt = datetime.combine(date, time)
            if timezone.is_naive(dt):
                dt = dt.replace(tzinfo=CEST)
            return dt.astimezone(timezone.utc)

        return None

    def set_status(self, new_status: str, user: User):
        if not user:
            raise ValueError(
                "A user must be provided to set_status for audit trail purposes."
            )

        old_status = None
        if self.pk:
            old_instance = self.__class__.objects.get(pk=self.pk)
            old_status = old_instance.status

        if old_status == new_status:
            logger.debug("No change for status", old_status, new_status)
            return

        with transaction.atomic():
            self.status = new_status
            self.save()

            AgendaChoreStatusChange.objects.create(
                agenda=self,
                user=user,
                status=new_status,
            )

    def save(self, *args, **kwargs):
        # Compute startdatetime from startdate and starttime (assumed CE(S)T)
        if self.startdate and self.starttime and not self.startdatetime:
            self.startdatetime = self._get_utc_from_cest_date_and_time(
                self.startdate, self.starttime
            )

        if self.enddate and self.endtime and not self.enddatetime:
            self.enddatetime = self._get_utc_from_cest_date_and_time(
                self.enddate, self.endtime
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_title}"


class AgendaChoreStatusChange(models.Model):
    agenda = models.ForeignKey("Agenda", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Agenda.STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Agenda Chore Status Change"
        verbose_name_plural = "Agenda Chore Status Changes"

    def __str__(self):
        return f"{self.user} set {self.agenda} to {self.status}"
