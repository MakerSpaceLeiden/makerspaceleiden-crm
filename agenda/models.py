from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from simple_history.models import HistoricalRecords

from chores.models import Chore
from members.models import User

CEST = ZoneInfo("Europe/Amsterdam")  # Handles both CET and CEST


class AgendaQuerySet(models.QuerySet):
    def upcoming_chores(self):
        return self.upcoming(chore__isnull=False)

    def upcoming(self, days=90, limit: int = None, **kwargs):
        today = timezone.now().date()
        end_date = today + timedelta(days=days)
        base_kwargs = kwargs.copy()
        start_q = Q(
            _startdatetime__gte=today, _startdatetime__lte=end_date, **base_kwargs
        )
        end_q = Q(_enddatetime__gte=today, **base_kwargs)
        return self.filter(start_q | end_q).order_by("_startdatetime", "item_title")[
            :limit
        ]


class Agenda(models.Model):
    _startdatetime = models.DateTimeField(null=True)
    startdate = models.DateField(null=True)
    starttime = models.TimeField(null=True)
    _enddatetime = models.DateTimeField(null=True)
    enddate = models.DateField(null=True)
    endtime = models.TimeField(null=True)
    item_title = models.TextField(max_length=600, default="")
    item_details = models.TextField(max_length=5000, blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    history = HistoricalRecords()

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    chore = models.ForeignKey(Chore, null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=None, null=True
    )

    objects = AgendaQuerySet.as_manager()

    @property
    def start_datetime(self):
        if self._startdatetime:
            return self._startdatetime
        if self.startdate and self.starttime:
            dt = datetime.combine(self.startdate, self.starttime)
            if timezone.is_naive(dt):
                dt = dt.replace(tzinfo=CEST)
            return dt.astimezone(timezone.utc)
        return None

    @property
    def end_datetime(self):
        if self._enddatetime:
            return self._enddatetime
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
            return None

        return self.status if self.status else "pending"

    @property
    def display_datetime(self) -> str:
        """
        Returns a string like 'Monday, 10-07 – 17-07' or just the start date if no end date.
        """
        if not self.start_datetime:
            return ""
        start_str = self.start_datetime.strftime("%A, %d-%m")
        if self.end_datetime:
            end_str = self.end_datetime.strftime("%d-%m")
            return f"{start_str} – {end_str}"
        return start_str

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

        if self.status == new_status:
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
        # Compute _startdatetime from startdate and starttime (assumed CE(S)T)
        if self.startdate and self.starttime and not self._startdatetime:
            self._startdatetime = self._get_utc_from_cest_date_and_time(
                self.startdate, self.starttime
            )

        if self.enddate and self.endtime and not self._enddatetime:
            self._enddatetime = self._get_utc_from_cest_date_and_time(
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
