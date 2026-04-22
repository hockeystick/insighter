from django.contrib.auth import get_user_model
from django.test import TestCase

from capabilities.models import (
    CapabilityItem,
    CapabilityState,
    Cluster,
    Outlet,
)


class AppendOnlyStateTests(TestCase):
    """State is append-only — current level = most recent row by set_at."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="specialist1", password="x")
        self.cluster = Cluster.objects.create(name="Segmentation", order=3)
        self.item = CapabilityItem.objects.create(cluster=self.cluster, name="Behavioural")
        self.outlet = Outlet.objects.create(name="Test Outlet", slug="test-outlet")

    def _append(self, level, evidence):
        return CapabilityState.objects.create(
            outlet=self.outlet,
            item=self.item,
            level=level,
            evidence_excerpt=evidence,
            set_by=self.user,
        )

    def test_current_state_is_most_recent_row(self):
        self._append(CapabilityState.LEVEL_AWARE, "heard of it")
        self._append(CapabilityState.LEVEL_PRACTISING, "running a first segmentation")

        current = (
            CapabilityState.objects
            .filter(outlet=self.outlet, item=self.item)
            .order_by("-set_at")
            .first()
        )
        self.assertEqual(current.level, CapabilityState.LEVEL_PRACTISING)

    def test_history_retained(self):
        self._append(CapabilityState.LEVEL_AWARE, "first pass")
        self._append(CapabilityState.LEVEL_PRACTISING, "second pass")
        self._append(CapabilityState.LEVEL_EMBEDDED, "third pass")

        rows = CapabilityState.objects.filter(outlet=self.outlet, item=self.item)
        self.assertEqual(rows.count(), 3)

    def test_evidence_excerpt_required(self):
        from django.core.exceptions import ValidationError
        state = CapabilityState(
            outlet=self.outlet,
            item=self.item,
            level=CapabilityState.LEVEL_AWARE,
            evidence_excerpt="",
            set_by=self.user,
        )
        with self.assertRaises(ValidationError):
            state.full_clean()
