"""Seed THROWAWAY stub outlets for smoke testing.

NOT the user's real seed outlets. Names and diagnostic text are
placeholder-grade. The user's three realistic seed outlets go in
`fixtures/demo_outlets.json` — see `fixtures/demo_outlets.example.json`.

This command is idempotent — safe to re-run. It creates 3 stub outlets
with tags lined up against the sponsors seeded by `seed_demo_refs`, a
handful of manual state changes per outlet so the grid renders, one
diagnostic per outlet, and a data champion on one so the bus-factor
indicator has variety to show.

Use for:
- Developer smoke testing (manage.py runserver + click through)
- CI end-to-end checks
- A judge reviewing the repo before you've seeded your real outlets

Delete stub outlets before recording the demo:

    python manage.py shell -c "
    from capabilities.models import Outlet
    Outlet.objects.filter(slug__startswith='stub-').delete()
    "
"""
from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from capabilities.models import CapabilityItem, CapabilityState, Outlet, SharedTag
from diagnostics.models import Diagnostic, Specialist


OUTLETS = [
    {
        "name": "[stub] La Gaceta del Barrio",
        "slug": "stub-la-gaceta",
        "cohort": "Wave 3",
        "enrolment_date": date(2026, 2, 1),
        "tag_values": [
            ("region", "Latin America"),
            ("language", "Spanish"),
            ("format", "Newsletter"),
            ("topic", "Local news"),
        ],
        "champion_username": "alma_segmentation",  # data champion in role
    },
    {
        "name": "[stub] Coastal Wire",
        "slug": "stub-coastal-wire",
        "cohort": "Wave 3",
        "enrolment_date": date(2026, 1, 15),
        "tag_values": [
            ("region", "West Africa"),
            ("language", "English"),
            ("language", "Swahili"),
            ("format", "Podcast"),
            ("topic", "Climate"),
        ],
        "champion_username": None,  # no champion — bus-factor risk
    },
    {
        "name": "[stub] Correio do Porto",
        "slug": "stub-correio-porto",
        "cohort": "Wave 2",
        "enrolment_date": date(2025, 11, 5),
        "tag_values": [
            ("region", "Southern Europe"),
            ("language", "Portuguese"),
            ("format", "Long-form print"),
            ("topic", "Investigative"),
            ("topic", "Economy"),
        ],
        "champion_username": None,
    },
]

# Keyed by outlet slug. Each entry: (item_pk, level, evidence, led_by_champion).
# Uses real CapabilityItem pks from the xlsx-generated taxonomy fixture.
STATE_CHANGES = {
    "stub-la-gaceta": [
        (1001, CapabilityState.LEVEL_PRACTISING,
         "Editorial team mapped their main touchpoints on a whiteboard during our call in March.", False),
        (1004, CapabilityState.LEVEL_EMBEDDED,
         "Lifecycle stages (anonymous > casual > registered > paying) baked into their CMS tags.", True),
        (4004, CapabilityState.LEVEL_PRACTISING,
         "Running a weekly behavioural segment review in GA4 since February.", False),
        (5002, CapabilityState.LEVEL_AWARE,
         "They've heard about engagement scoring but haven't built one.", False),
    ],
    "stub-coastal-wire": [
        (1001, CapabilityState.LEVEL_AWARE,
         "We talked about touchpoint mapping but nothing formal yet.", False),
        (7001, CapabilityState.LEVEL_PRACTISING,
         "Attribution report pulled last month; Instagram and WhatsApp are the dominant sources.", False),
        (7004, CapabilityState.LEVEL_PRACTISING,
         "Testing Facebook ad spend monthly with a small budget; tracking CPA per campaign.", False),
        (5005, CapabilityState.LEVEL_UNKNOWN,
         "Retention metrics not discussed in last diagnostic; no signal either way.", False),
    ],
    "stub-correio-porto": [
        (8002, CapabilityState.LEVEL_EMBEDDED,
         "Full GDPR mapping complete, double opt-in on all newsletters, reviewed quarterly.", False),
        (8005, CapabilityState.LEVEL_PRACTISING,
         "Running monthly bounce handling and list cleaning since last quarter.", False),
        (12001, CapabilityState.LEVEL_AWARE,
         "Team metrics training discussed but no sessions scheduled yet.", False),
    ],
}

DIAGNOSTIC_NOTES = {
    "stub-la-gaceta": (
        "Call with El Norte's managing editor — they're pushing hard on retention for registered users. "
        "Walked through their segmentation work: behavioural segment review runs every Tuesday, lifecycle "
        "stages baked into CMS. Data champion Ana owns the dashboard. Talked about engagement scoring — "
        "they know what it is but haven't stood it up. No touchpoint map beyond whiteboard sketches."
    ),
    "stub-coastal-wire": (
        "Diagnostic with Coastal Wire. Their stated priority is audience growth — want to push hard on "
        "acquisition. They're running Instagram Reels and WhatsApp broadcasts, testing paid ads monthly. "
        "No one on the team is formally carrying the data work; managing editor does it herself. "
        "Didn't get to retention or churn this call."
    ),
    "stub-correio-porto": (
        "Long diagnostic with Correio do Porto. They want to professionalise on the compliance side — "
        "GDPR is tight, list hygiene is running monthly. Asked about data literacy training for the "
        "newsroom; they're open to it but nothing scheduled. Champion role unclear — the CTO is "
        "carrying all the tooling but doesn't see himself as a data champion."
    ),
}


class Command(BaseCommand):
    help = "Seed throwaway stub outlets for smoke testing. Does NOT touch your real seed outlets."

    def handle(self, *args, **options):
        User = get_user_model()

        # Make sure there's a user to conduct diagnostics and set states.
        # Prefer a seeded specialist; fall back to any staff user; fall back to creating one.
        conductor = None
        try:
            conductor = Specialist.objects.select_related("user").first().user
        except (Specialist.DoesNotExist, AttributeError):
            conductor = User.objects.filter(is_staff=True).first()
        if conductor is None:
            conductor = User.objects.create_user(
                username="stub_conductor", is_staff=True, is_active=True
            )

        tag_lookup: dict[tuple[str, str], SharedTag] = {}

        def resolve_tag(dim: str, value: str) -> SharedTag:
            key = (dim, value)
            if key not in tag_lookup:
                tag_lookup[key], _ = SharedTag.objects.get_or_create(
                    dimension=dim, value=value
                )
            return tag_lookup[key]

        outlet_count = 0
        for spec in OUTLETS:
            outlet, created = Outlet.objects.get_or_create(
                slug=spec["slug"],
                defaults={
                    "name": spec["name"],
                    "cohort": spec["cohort"],
                    "enrolment_date": spec["enrolment_date"],
                },
            )
            if not created:
                outlet.name = spec["name"]
                outlet.cohort = spec["cohort"]
                outlet.enrolment_date = spec["enrolment_date"]
            # Attach tags
            outlet.tags.set([resolve_tag(d, v) for d, v in spec["tag_values"]])
            # Data champion
            if spec["champion_username"]:
                champion_user, _ = User.objects.get_or_create(
                    username=spec["champion_username"],
                    defaults={"is_staff": True, "is_active": True},
                )
                outlet.data_champion = champion_user
            else:
                outlet.data_champion = None
            outlet.save()
            outlet_count += int(created)

            # Seed a diagnostic (one per outlet, idempotent by date+outlet)
            diag_date = (outlet.enrolment_date or date.today()) + timedelta(days=45)
            diag, _ = Diagnostic.objects.get_or_create(
                outlet=outlet,
                date=diag_date,
                defaults={
                    "conducted_by": conductor,
                    "notes_raw": DIAGNOSTIC_NOTES[outlet.slug],
                    "status": Diagnostic.STATUS_COMMITTED,
                },
            )

            # Seed state changes — wipe prior state to keep re-runs idempotent.
            outlet.states.all().delete()
            for item_pk, level, evidence, champion in STATE_CHANGES.get(outlet.slug, []):
                try:
                    item = CapabilityItem.objects.get(pk=item_pk)
                except CapabilityItem.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"  skip: no CapabilityItem pk={item_pk} for {outlet.name}"
                    ))
                    continue
                CapabilityState.objects.create(
                    outlet=outlet,
                    item=item,
                    level=level,
                    led_by_champion=champion,
                    evidence_excerpt=evidence,
                    set_by=conductor,
                    source_diagnostic=diag,
                )

        self.stdout.write(self.style.SUCCESS(
            f"Stub outlets: {outlet_count} created, {Outlet.objects.filter(slug__startswith='stub-').count()} total stubs "
            f"(out of {Outlet.objects.count()} outlets overall)."
        ))
        self.stdout.write(self.style.WARNING(
            "These are placeholders. Delete them (Outlet.objects.filter(slug__startswith='stub-').delete()) "
            "before recording your demo; the real seed outlets go in fixtures/demo_outlets.json."
        ))
