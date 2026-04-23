from django.conf import settings
from django.db import models


class SharedTag(models.Model):
    """Taxonomy term shared across Outlet / Specialist / Sponsor for matching."""

    DIMENSION_REGION = "region"
    DIMENSION_LANGUAGE = "language"
    DIMENSION_FORMAT = "format"
    DIMENSION_TOPIC = "topic"
    DIMENSION_CHOICES = [
        (DIMENSION_REGION, "Region"),
        (DIMENSION_LANGUAGE, "Language"),
        (DIMENSION_FORMAT, "Format"),
        (DIMENSION_TOPIC, "Topic"),
    ]

    dimension = models.CharField(max_length=16, choices=DIMENSION_CHOICES)
    value = models.CharField(max_length=128)

    class Meta:
        unique_together = [("dimension", "value")]
        ordering = ["dimension", "value"]

    def __str__(self):
        return f"{self.get_dimension_display()}: {self.value}"


class Cluster(models.Model):
    """A capability cluster within a desk's taxonomy."""

    DESK_AUDIENCE_DEV = "audience_development"
    DESK_CHOICES = [
        (DESK_AUDIENCE_DEV, "Audience Development"),
    ]

    desk = models.CharField(
        max_length=64,
        choices=DESK_CHOICES,
        default=DESK_AUDIENCE_DEV,
    )
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["desk", "order", "name"]
        unique_together = [("desk", "name")]

    def __str__(self):
        return f"{self.name}"


class CapabilityItem(models.Model):
    """A single capability within a cluster, with metadata that drives tracker behaviour."""

    PRIORITY_HIGH = "H"
    PRIORITY_MEDIUM = "M"
    PRIORITY_LOW = "L"
    PRIORITY_CHOICES = [
        (PRIORITY_HIGH, "High"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_LOW, "Low"),
    ]

    PHASE_ADVISORY = "advisory"
    PHASE_ACTIVATION = "activation"
    PHASE_RESOURCES = "resources"
    PHASE_CHOICES = [
        (PHASE_ADVISORY, "Advisory"),
        (PHASE_ACTIVATION, "Activation"),
        (PHASE_RESOURCES, "Resources"),
    ]

    ASSESSMENT_INTERVIEW = "interview"
    ASSESSMENT_SURVEY = "survey"
    ASSESSMENT_FILE = "file_transfer"
    ASSESSMENT_AUTOMATED = "automated"
    ASSESSMENT_CHOICES = [
        (ASSESSMENT_INTERVIEW, "Interview"),
        (ASSESSMENT_SURVEY, "Survey"),
        (ASSESSMENT_FILE, "File transfer"),
        (ASSESSMENT_AUTOMATED, "Automated"),
    ]

    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default=PRIORITY_MEDIUM)
    baseline = models.BooleanField(default=False, help_text="Expected of every outlet by exit.")
    template_able = models.BooleanField(default=False, help_text="Artefact is reusable across outlets.")
    phase = models.CharField(max_length=16, choices=PHASE_CHOICES, default=PHASE_ADVISORY)
    assessment_method = models.CharField(max_length=16, choices=ASSESSMENT_CHOICES, default=ASSESSMENT_INTERVIEW)
    cross_desk_dep = models.CharField(
        max_length=128,
        blank=True,
        help_text="Free-text pointer to another desk's capability when progress here is gated elsewhere.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["cluster", "order", "name"]
        unique_together = [("cluster", "name")]

    def __str__(self):
        return f"{self.cluster.name} / {self.name}"

    @property
    def subcluster(self) -> str:
        """L2 subcluster, parsed from the description prefix set by the ingest script."""
        for line in self.description.splitlines():
            if line.startswith("Subcluster:"):
                return line.split(":", 1)[1].strip()
        return ""


class Outlet(models.Model):
    """A newsroom enrolled in the programme."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    cohort = models.CharField(max_length=64, blank=True, help_text="Wave / cohort label.")
    enrolment_date = models.DateField(null=True, blank=True)
    exit_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    data_champion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="champions_at",
        help_text="Outlet-side person carrying practice forward post-handover (Bus Factor).",
    )

    tags = models.ManyToManyField(SharedTag, blank=True, related_name="outlets")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CapabilityState(models.Model):
    """Append-only log of capability state changes per outlet.

    Current state for (outlet, item) is the most recent row by set_at.
    No row is ever mutated or deleted in normal flow.

    `level` captures depth of practice. `led_by_champion` captures bus-factor
    at the capability (is an outlet-side data champion sustaining it?). The
    two were initially fused into a single enum; separating them keeps the
    Bus-Factor KPI legible without overloading the depth scale.
    """

    LEVEL_UNKNOWN = 0
    LEVEL_AWARE = 1
    LEVEL_PRACTISING = 2
    LEVEL_EMBEDDED = 3
    LEVEL_CHOICES = [
        (LEVEL_UNKNOWN, "Unknown"),
        (LEVEL_AWARE, "Aware"),
        (LEVEL_PRACTISING, "Practising"),
        (LEVEL_EMBEDDED, "Embedded"),
    ]

    outlet = models.ForeignKey(Outlet, on_delete=models.CASCADE, related_name="states")
    item = models.ForeignKey(CapabilityItem, on_delete=models.CASCADE, related_name="states")
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES, default=LEVEL_UNKNOWN)
    led_by_champion = models.BooleanField(
        default=False,
        help_text="This capability is currently sustained by an outlet-side data champion (Bus Factor).",
    )
    evidence_excerpt = models.TextField(
        help_text="Quoted evidence from the diagnostic — required, no empty rows.",
    )

    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="states_set",
    )
    set_at = models.DateTimeField(auto_now_add=True)

    source_diagnostic = models.ForeignKey(
        "diagnostics.Diagnostic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="state_changes",
    )
    llm_proposed = models.BooleanField(default=False)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="states_accepted",
    )

    class Meta:
        ordering = ["-set_at"]
        indexes = [
            models.Index(fields=["outlet", "item", "-set_at"]),
        ]

    def __str__(self):
        return f"{self.outlet} / {self.item} → {self.get_level_display()} @ {self.set_at:%Y-%m-%d}"
