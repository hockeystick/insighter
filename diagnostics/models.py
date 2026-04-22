from django.conf import settings
from django.db import models

from capabilities.models import Outlet, SharedTag


class Diagnostic(models.Model):
    """A diagnostic call with an outlet. Source of truth for state changes."""

    STATUS_DRAFT = "draft"
    STATUS_COMMITTED = "committed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_COMMITTED, "Committed"),
    ]

    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name="diagnostics")
    date = models.DateField()
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="diagnostics_conducted",
    )
    notes_raw = models.TextField(help_text="Raw call notes — the source document for state synthesis.")
    notes_summary = models.TextField(blank=True)
    llm_proposals_json = models.JSONField(null=True, blank=True, help_text="Cached tool-call output from synthesis run.")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.outlet} diagnostic {self.date:%Y-%m-%d}"


class Specialist(models.Model):
    """Programme specialist deployable to outlets. Stub in v0.1."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="specialist_profile")
    display_name = models.CharField(max_length=200)
    tags = models.ManyToManyField(SharedTag, blank=True, related_name="specialists")
    availability_hours_per_week = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_name"]

    def __str__(self):
        return self.display_name


class Deployment(models.Model):
    """Who is doing what with which outlet. Stub in v0.1 — schema only."""

    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name="deployments")
    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name="deployments")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    hours_committed = models.PositiveSmallIntegerField(default=0)
    handover_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.specialist} → {self.outlet} ({self.start_date})"


class CheckIn(models.Model):
    """30/60/90-day behavioural check-in post-handover. Stub in v0.1 — schema only."""

    MILESTONE_30 = 30
    MILESTONE_60 = 60
    MILESTONE_90 = 90
    MILESTONE_CHOICES = [
        (MILESTONE_30, "30 days"),
        (MILESTONE_60, "60 days"),
        (MILESTONE_90, "90 days"),
    ]

    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name="checkins")
    milestone_day = models.PositiveSmallIntegerField(choices=MILESTONE_CHOICES)
    scheduled_for = models.DateField()
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checkins_responded",
    )
    behavioural_answers = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-scheduled_for"]
        unique_together = [("outlet", "milestone_day")]

    def __str__(self):
        return f"{self.outlet} {self.milestone_day}d check-in"


class Sponsor(models.Model):
    """Funder tagged against the dimensions they fund. Stub in v0.1."""

    name = models.CharField(max_length=200)
    funding_notes = models.TextField(blank=True)
    tags = models.ManyToManyField(SharedTag, blank=True, related_name="sponsors")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
