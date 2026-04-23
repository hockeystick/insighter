"""Seed SharedTags, Sponsors, and Specialists for the demo.

Idempotent — safe to re-run. Does NOT touch outlets or diagnostics; those stay
under the user's control.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from capabilities.models import SharedTag
from diagnostics.models import Specialist, Sponsor

TAGS = {
    SharedTag.DIMENSION_REGION: [
        "North America", "Latin America", "West Africa", "East Africa",
        "Western Europe", "Southern Europe", "South Asia", "Southeast Asia",
    ],
    SharedTag.DIMENSION_LANGUAGE: [
        "English", "Spanish", "French", "Portuguese", "Arabic", "Swahili", "Urdu",
    ],
    SharedTag.DIMENSION_FORMAT: [
        "Newsletter", "Podcast", "Long-form print", "Short video", "Radio",
    ],
    SharedTag.DIMENSION_TOPIC: [
        "Climate", "Local news", "Investigative", "Health", "Economy", "Civic tech",
    ],
}

SPONSORS = [
    {
        "name": "Meridian Fund",
        "funding_notes": "Funds Spanish-language local and investigative work across the Americas.",
        "tag_values": [
            ("region", "Latin America"),
            ("region", "North America"),
            ("language", "Spanish"),
            ("topic", "Local news"),
            ("topic", "Investigative"),
        ],
    },
    {
        "name": "Kiln Climate Media",
        "funding_notes": "Climate coverage in the Global South. Prefers newsletter and podcast formats.",
        "tag_values": [
            ("region", "West Africa"),
            ("region", "South Asia"),
            ("region", "Southeast Asia"),
            ("topic", "Climate"),
            ("format", "Newsletter"),
            ("format", "Podcast"),
        ],
    },
    {
        "name": "Civic Audio Collective",
        "funding_notes": "Audio journalism in under-served languages.",
        "tag_values": [
            ("language", "Swahili"),
            ("language", "Urdu"),
            ("language", "Arabic"),
            ("format", "Podcast"),
            ("format", "Radio"),
            ("topic", "Civic tech"),
        ],
    },
    {
        "name": "Open Europe Trust",
        "funding_notes": "European newsrooms, cross-language investigative work.",
        "tag_values": [
            ("region", "Western Europe"),
            ("region", "Southern Europe"),
            ("language", "French"),
            ("language", "Portuguese"),
            ("topic", "Investigative"),
            ("topic", "Economy"),
        ],
    },
]

SPECIALISTS = [
    {
        "username": "alma_segmentation",
        "display_name": "Alma Reyes",
        "hours": 16,
        "tag_values": [
            ("region", "Latin America"),
            ("language", "Spanish"),
            ("topic", "Local news"),
            ("format", "Newsletter"),
        ],
    },
    {
        "username": "kwame_audio",
        "display_name": "Kwame Adjei",
        "hours": 12,
        "tag_values": [
            ("region", "West Africa"),
            ("region", "East Africa"),
            ("language", "English"),
            ("language", "Swahili"),
            ("format", "Podcast"),
            ("format", "Radio"),
        ],
    },
    {
        "username": "priya_climate",
        "display_name": "Priya Menon",
        "hours": 20,
        "tag_values": [
            ("region", "South Asia"),
            ("region", "Southeast Asia"),
            ("topic", "Climate"),
            ("topic", "Health"),
            ("format", "Newsletter"),
        ],
    },
    {
        "username": "luca_investigative",
        "display_name": "Luca Romano",
        "hours": 14,
        "tag_values": [
            ("region", "Southern Europe"),
            ("region", "Western Europe"),
            ("language", "French"),
            ("language", "Portuguese"),
            ("topic", "Investigative"),
            ("topic", "Economy"),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed SharedTags, Sponsors, and Specialists for the demo. Idempotent."

    def handle(self, *args, **options):
        # Tags
        tag_count = 0
        for dim, values in TAGS.items():
            for value in values:
                _, created = SharedTag.objects.get_or_create(dimension=dim, value=value)
                tag_count += int(created)
        self.stdout.write(self.style.SUCCESS(f"Tags: {tag_count} created, {SharedTag.objects.count()} total."))

        def _resolve_tags(pairs):
            return [SharedTag.objects.get(dimension=d, value=v) for d, v in pairs]

        sponsor_count = 0
        for spec in SPONSORS:
            sponsor, created = Sponsor.objects.get_or_create(
                name=spec["name"],
                defaults={"funding_notes": spec["funding_notes"]},
            )
            if not created:
                sponsor.funding_notes = spec["funding_notes"]
                sponsor.save(update_fields=["funding_notes"])
            sponsor.tags.set(_resolve_tags(spec["tag_values"]))
            sponsor_count += int(created)
        self.stdout.write(self.style.SUCCESS(f"Sponsors: {sponsor_count} created, {Sponsor.objects.count()} total."))

        User = get_user_model()
        specialist_count = 0
        for spec in SPECIALISTS:
            user, _ = User.objects.get_or_create(
                username=spec["username"],
                defaults={"is_staff": True, "is_active": True},
            )
            specialist, created = Specialist.objects.get_or_create(
                user=user,
                defaults={
                    "display_name": spec["display_name"],
                    "availability_hours_per_week": spec["hours"],
                },
            )
            if not created:
                specialist.display_name = spec["display_name"]
                specialist.availability_hours_per_week = spec["hours"]
                specialist.save(update_fields=["display_name", "availability_hours_per_week"])
            specialist.tags.set(_resolve_tags(spec["tag_values"]))
            specialist_count += int(created)
        self.stdout.write(self.style.SUCCESS(f"Specialists: {specialist_count} created, {Specialist.objects.count()} total."))

        self.stdout.write(self.style.SUCCESS("Done. Seed your outlets in admin and tag them against the same SharedTags to see sponsor matches."))
