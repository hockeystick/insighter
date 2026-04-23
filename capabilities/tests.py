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


class WhyStuckTests(TestCase):
    """Composed 'why is this outlet stuck' view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="staff2", password="x")
        cls.outlet = Outlet.objects.create(name="La Voz", slug="la-voz", cohort="Wave 2")
        cluster = Cluster.objects.create(name="Retention", order=5)
        cls.item = CapabilityItem.objects.create(cluster=cluster, name="Churn prevention", order=4)

    def setUp(self):
        self.client.login(username="staff2", password="x")

    def test_renders_without_mismatch_cache(self):
        resp = self.client.get(reverse("capabilities:why_stuck", args=[self.outlet.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Why is this outlet stuck")
        self.assertContains(resp, "Retention")
        self.assertContains(resp, "No mismatch check run yet")

    def test_renders_cached_mismatch(self):
        from django.utils import timezone
        self.outlet.mismatch_flag_json = {
            "headline": "Outlet says retention, does acquisition.",
            "flags": [
                {
                    "title": "Priority/evidence drift",
                    "narrative": "Stated retention focus but 4 of last 5 state changes are in acquisition.",
                    "severity": "high",
                }
            ],
            "bus_factor_risk": "Data champion unfilled; all state changes set by programme staff.",
            "model": "claude-opus-4-7",
            "usage": {"cache_read_input_tokens": 5000},
        }
        self.outlet.mismatch_flag_computed_at = timezone.now()
        self.outlet.save()

        resp = self.client.get(reverse("capabilities:why_stuck", args=[self.outlet.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Priority/evidence drift")
        self.assertContains(resp, "Data champion unfilled")
        self.assertContains(resp, "claude-opus-4-7")

    def test_mismatch_run_blocked_without_api_key(self):
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        resp = self.client.post(reverse("capabilities:mismatch_run", args=[self.outlet.slug]))
        self.assertEqual(resp.status_code, 503)


class SponsorMatcherTests(TestCase):
    """Tag-overlap ranking across Sponsor / Outlet / Specialist."""

    @classmethod
    def setUpTestData(cls):
        from diagnostics.models import Sponsor, Specialist
        from capabilities.models import SharedTag

        User = get_user_model()
        cls.user = User.objects.create_user(username="staff3", password="x")
        cls.lat_am = SharedTag.objects.create(dimension=SharedTag.DIMENSION_REGION, value="Latin America")
        cls.spanish = SharedTag.objects.create(dimension=SharedTag.DIMENSION_LANGUAGE, value="Spanish")
        cls.local = SharedTag.objects.create(dimension=SharedTag.DIMENSION_TOPIC, value="Local news")
        cls.climate = SharedTag.objects.create(dimension=SharedTag.DIMENSION_TOPIC, value="Climate")

        cls.sponsor = Sponsor.objects.create(name="Meridian Fund")
        cls.sponsor.tags.set([cls.lat_am, cls.spanish, cls.local])

        cls.outlet_match = Outlet.objects.create(name="El Norte", slug="el-norte")
        cls.outlet_match.tags.set([cls.lat_am, cls.spanish])

        cls.outlet_miss = Outlet.objects.create(name="Kilkenny Post", slug="kilkenny")
        cls.outlet_miss.tags.set([cls.climate])

        alma = User.objects.create_user(username="alma", password="x")
        cls.specialist = Specialist.objects.create(user=alma, display_name="Alma R.")
        cls.specialist.tags.set([cls.lat_am, cls.spanish])

    def setUp(self):
        self.client.login(username="staff3", password="x")

    def test_sponsor_match_index_lists_sponsors(self):
        resp = self.client.get(reverse("capabilities:sponsor_match_index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Meridian Fund")

    def test_sponsor_detail_ranks_by_overlap_and_excludes_zero_overlap(self):
        resp = self.client.get(reverse("capabilities:sponsor_match_detail", args=[self.sponsor.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "El Norte")
        self.assertNotContains(resp, "Kilkenny Post")
        self.assertContains(resp, "Alma R.")
        # El Norte overlaps on 2 tags (Latin America + Spanish)
        self.assertContains(resp, "2 matches")


class StubScreenTests(TestCase):
    """Deployment + CheckIn list views render with empty state and with data."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="stubs", password="x")

    def setUp(self):
        self.client.login(username="stubs", password="x")

    def test_deployment_list_empty(self):
        resp = self.client.get(reverse("capabilities:deployment_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No deployments")

    def test_checkin_list_empty(self):
        resp = self.client.get(reverse("capabilities:checkin_list"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No check-ins")


class TaxonomyBrowserTests(TestCase):
    """Public read-only taxonomy view + subcluster parsing."""

    @classmethod
    def setUpTestData(cls):
        cls.cluster = Cluster.objects.create(name="Service design", order=1)
        cls.with_sub = CapabilityItem.objects.create(
            cluster=cls.cluster,
            name="Map current touchpoints",
            description="Subcluster: Service blueprint\nNotes: foundation",
            order=1,
        )
        cls.no_sub = CapabilityItem.objects.create(
            cluster=cls.cluster,
            name="Ungrouped item",
            description="",
            order=2,
        )

    def test_subcluster_property_parses_prefix(self):
        self.assertEqual(self.with_sub.subcluster, "Service blueprint")
        self.assertEqual(self.no_sub.subcluster, "")

    def test_taxonomy_browser_is_public(self):
        resp = self.client.get(reverse("capabilities:taxonomy_browser"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Service design")
        self.assertContains(resp, "Service blueprint")
        self.assertContains(resp, "Map current touchpoints")
