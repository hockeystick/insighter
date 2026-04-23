from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from capabilities.models import (
    CapabilityItem,
    CapabilityState,
    Cluster,
    Outlet,
)
from diagnostics.models import Diagnostic


def _fake_anthropic_response(proposals, *, cache_read=5000, cache_write=0, input_tokens=400):
    """Build a minimal stand-in for an Anthropic `messages.create` response."""
    tool_use = SimpleNamespace(
        type="tool_use",
        name="propose_state_changes",
        input={"proposals": proposals},
    )
    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=220,
        cache_read_input_tokens=cache_read,
        cache_creation_input_tokens=cache_write,
    )
    return SimpleNamespace(
        content=[tool_use],
        stop_reason="tool_use",
        model="claude-opus-4-7",
        usage=usage,
    )


class SynthesisFlowTests(TestCase):
    """Full synthesis loop with a mocked Anthropic client."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="specialist", password="x")
        cls.outlet = Outlet.objects.create(name="El Norte", slug="el-norte", cohort="Wave 3")
        cls.cluster = Cluster.objects.create(name="Segmentation", order=3)
        cls.item_a = CapabilityItem.objects.create(
            cluster=cls.cluster,
            name="Behavioural segmentation",
            description="Subcluster: Behavioural",
            order=1,
        )
        cls.item_b = CapabilityItem.objects.create(
            cluster=cls.cluster,
            name="New vs returning",
            description="Subcluster: New vs returning",
            order=3,
        )

    def setUp(self):
        self.client.login(username="specialist", password="x")
        self.diagnostic = Diagnostic.objects.create(
            outlet=self.outlet,
            date="2026-04-23",
            conducted_by=self.user,
            notes_raw="They ran a segment review on Tuesday. New vs returning not tracked yet.",
        )

    def _run_synthesis_with(self, proposals):
        fake = SimpleNamespace(
            messages=SimpleNamespace(create=lambda **kwargs: _fake_anthropic_response(proposals))
        )
        patcher = patch("diagnostics.views.run_synthesis", side_effect=lambda diagnostic: {
            "proposals": proposals,
            "model": "claude-opus-4-7",
            "stop_reason": "tool_use",
            "usage": {
                "input_tokens": 400,
                "output_tokens": 220,
                "cache_read_input_tokens": 5000,
                "cache_creation_input_tokens": 0,
            },
        })
        return patcher, fake

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    def test_synthesis_run_stores_proposals_and_redirects_to_review(self):
        proposals = [
            {
                "item_id": self.item_a.id,
                "proposed_level": "Practising",
                "led_by_champion": False,
                "evidence_excerpt": "They ran a segment review on Tuesday.",
                "confidence": 4,
                "rationale": "Concrete recent execution evidence.",
            }
        ]
        patcher, _ = self._run_synthesis_with(proposals)
        with patcher:
            resp = self.client.post(
                reverse("diagnostics:synthesis_run", args=[self.diagnostic.pk])
            )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/synthesis/review/", resp.url)
        self.diagnostic.refresh_from_db()
        self.assertEqual(
            self.diagnostic.llm_proposals_json["proposals"][0]["item_id"], self.item_a.id
        )

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    def test_synthesis_review_page_renders_proposals(self):
        self.diagnostic.llm_proposals_json = {
            "proposals": [
                {
                    "item_id": self.item_a.id,
                    "proposed_level": "Practising",
                    "led_by_champion": False,
                    "evidence_excerpt": "They ran a segment review on Tuesday.",
                    "confidence": 4,
                    "rationale": "Concrete execution.",
                }
            ],
            "usage": {"cache_read_input_tokens": 5000},
            "model": "claude-opus-4-7",
        }
        self.diagnostic.save()

        resp = self.client.get(
            reverse("diagnostics:synthesis_review", args=[self.diagnostic.pk])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Behavioural segmentation")
        self.assertContains(resp, "They ran a segment review on Tuesday.")
        self.assertContains(resp, "claude-opus-4-7")

    def test_synthesis_accept_creates_state_rows_only_for_accepted(self):
        self.diagnostic.llm_proposals_json = {
            "proposals": [
                {
                    "item_id": self.item_a.id,
                    "proposed_level": "Practising",
                    "led_by_champion": False,
                    "evidence_excerpt": "They ran a segment review on Tuesday.",
                    "confidence": 4,
                    "rationale": "",
                },
                {
                    "item_id": self.item_b.id,
                    "proposed_level": "Aware",
                    "led_by_champion": False,
                    "evidence_excerpt": "New vs returning not tracked yet.",
                    "confidence": 3,
                    "rationale": "",
                },
            ]
        }
        self.diagnostic.save()

        resp = self.client.post(
            reverse("diagnostics:synthesis_accept", args=[self.diagnostic.pk]),
            {
                f"action_{self.item_a.id}": "accept",
                f"level_{self.item_a.id}": "Embedded",
                f"evidence_{self.item_a.id}": "They ran a segment review on Tuesday.",
                f"champion_{self.item_a.id}": "on",
                f"action_{self.item_b.id}": "reject",
            },
        )
        self.assertEqual(resp.status_code, 302)

        rows = CapabilityState.objects.filter(outlet=self.outlet)
        self.assertEqual(rows.count(), 1)
        row = rows.get()
        self.assertEqual(row.item_id, self.item_a.id)
        self.assertEqual(row.level, CapabilityState.LEVEL_EMBEDDED)  # user-edited
        self.assertTrue(row.led_by_champion)
        self.assertTrue(row.llm_proposed)
        self.assertEqual(row.accepted_by, self.user)
        self.assertEqual(row.source_diagnostic, self.diagnostic)

        self.diagnostic.refresh_from_db()
        self.assertEqual(self.diagnostic.status, Diagnostic.STATUS_COMMITTED)

    def test_synthesis_run_blocked_without_api_key(self):
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        resp = self.client.post(
            reverse("diagnostics:synthesis_run", args=[self.diagnostic.pk])
        )
        self.assertEqual(resp.status_code, 503)
        self.assertContains(resp, "ANTHROPIC_API_KEY", status_code=503)


class SynthesisPromptAssemblyTests(TestCase):
    """Unit tests on the prompt builders — no API calls."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="u1", password="x")
        cls.outlet = Outlet.objects.create(name="Foo", slug="foo")
        cls.cluster = Cluster.objects.create(name="Segmentation", order=3)
        cls.item = CapabilityItem.objects.create(
            cluster=cls.cluster,
            name="Behavioural",
            description="Subcluster: Behavioural\nNotes: a note",
            priority="H",
            baseline=True,
            phase="activation",
            order=1,
        )

    def test_format_taxonomy_is_deterministic_and_includes_ids(self):
        from insighter.llm.synthesis import _format_taxonomy

        first = _format_taxonomy()
        second = _format_taxonomy()
        self.assertEqual(first, second, "Taxonomy serialization must be byte-stable for cache hits.")
        self.assertIn(f"item_id={self.item.id}", first)
        self.assertIn("priority=High", first)
        self.assertIn("baseline", first)
        self.assertIn("phase=Activation", first)

    def test_format_outlet_state_with_no_history(self):
        from insighter.llm.synthesis import _format_outlet_state

        text = _format_outlet_state(self.outlet)
        self.assertIn("No capability state recorded yet", text)
        self.assertIn("UNFILLED", text)  # no data champion
