from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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

    def test_champion_flag_independent_of_level(self):
        state = CapabilityState.objects.create(
            outlet=self.outlet,
            item=self.item,
            level=CapabilityState.LEVEL_PRACTISING,
            evidence_excerpt="data champion running weekly reviews",
            led_by_champion=True,
            set_by=self.user,
        )
        self.assertTrue(state.led_by_champion)
        self.assertEqual(state.level, CapabilityState.LEVEL_PRACTISING)

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


class ViewSmokeTests(TestCase):
    """End-to-end GET-200 on the core v0.1 screens, authenticated."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="staff", password="x")
        cls.outlet = Outlet.objects.create(name="El Norte", slug="el-norte", cohort="Wave 3")
        cluster = Cluster.objects.create(name="Segmentation", order=3)
        cls.item = CapabilityItem.objects.create(cluster=cluster, name="Behavioural")

    def setUp(self):
        self.client.login(username="staff", password="x")

    def test_outlet_list_renders(self):
        resp = self.client.get(reverse("capabilities:outlet_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "El Norte")

    def test_outlet_detail_renders(self):
        resp = self.client.get(reverse("capabilities:outlet_detail", args=[self.outlet.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Segmentation")
        self.assertContains(resp, "Behavioural")

    def test_state_create_appends_row(self):
        resp = self.client.post(
            reverse("capabilities:state_create", args=[self.outlet.slug]),
            {
                "item": self.item.id,
                "level": CapabilityState.LEVEL_PRACTISING,
                "evidence_excerpt": "they ran a segment review last week",
                "source_diagnostic": "",
            },
        )
        self.assertEqual(resp.status_code, 302)
        state = CapabilityState.objects.get(outlet=self.outlet, item=self.item)
        self.assertEqual(state.level, CapabilityState.LEVEL_PRACTISING)
        self.assertEqual(state.set_by, self.user)

    def test_diagnostic_create_redirects_to_detail(self):
        resp = self.client.post(
            reverse("diagnostics:diagnostic_create", args=[self.outlet.slug]),
            {
                "date": "2026-04-22",
                "notes_raw": "We talked about their segmentation work.",
                "notes_summary": "",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/diagnostics/", resp.url)

    def test_login_required_redirect(self):
        self.client.logout()
        resp = self.client.get(reverse("capabilities:outlet_list"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/admin/login/", resp.url)
