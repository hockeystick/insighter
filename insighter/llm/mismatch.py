"""Intent-vs-evidence mismatch flagger.

Cross-references the outlet's most recent diagnostic notes (for stated priorities)
against the trajectory of capability state changes and the data-champion presence,
then returns narrative flags via tool-use.

This is the load-bearing "why Opus 4.7" demo beat: cross-referential semantic
reading against structured state. Rule-based matching can't do it.
"""
from __future__ import annotations

from typing import Any

from capabilities.models import CapabilityState, Outlet
from diagnostics.models import Diagnostic
from insighter.llm.client import EFFORT, MAX_TOKENS, MODEL, get_client
from insighter.llm.synthesis import _format_taxonomy

TOOL_NAME = "report_mismatches"

TOOL_SCHEMA: dict[str, Any] = {
    "name": TOOL_NAME,
    "description": (
        "Report mismatches between what the outlet says it cares about and what "
        "its capability state history shows. Each flag is a short narrative."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "headline": {
                "type": "string",
                "description": (
                    "One-sentence summary of the biggest gap. If nothing is "
                    "mismatched, say so plainly. Avoid hedging."
                ),
            },
            "flags": {
                "type": "array",
                "description": (
                    "Specific mismatches. Empty if there are none. Each flag is "
                    "self-contained — readable in isolation."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short label, 3-8 words.",
                        },
                        "narrative": {
                            "type": "string",
                            "description": (
                                "2-4 sentences. Cite the stated priority, then "
                                "the evidence from state history that "
                                "contradicts or undercuts it. Reference cluster "
                                "names or item names where specific."
                            ),
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "description": (
                                "high = blocks the outlet's stated goal; "
                                "medium = material drag; low = worth noting."
                            ),
                        },
                    },
                    "required": ["title", "narrative", "severity"],
                    "additionalProperties": False,
                },
            },
            "bus_factor_risk": {
                "type": "string",
                "description": (
                    "One or two sentences on whether the outlet looks dependent "
                    "on programme staff or is growing its own capacity. Cite "
                    "data-champion presence and whether recent state changes "
                    "include led_by_champion=true. Empty string if you can't tell."
                ),
            },
        },
        "required": ["headline", "flags", "bus_factor_risk"],
        "additionalProperties": False,
    },
}

SYSTEM_PROMPT = """You read newsroom service-desk data and flag places where an outlet's stated priorities don't match the evidence of what they're actually doing. You do not give advice; you report gaps.

Judging calls you'll make:
- Stated priorities come from diagnostic narrative — what the outlet said they care about, what they asked for help on, what they framed as urgent.
- Evidence comes from capability state changes over time — which clusters have movement, which are stalled, where the data champion is carrying load.
- A mismatch is a contradiction or drag. Example: outlet says retention is the priority; 4 of the last 5 state changes are in acquisition; no movement on churn prevention in 60 days. That's a mismatch.
- Being early / at low depth is not a mismatch on its own. Mismatch is about direction, not current level.

Rules:
- Be specific. Name clusters or item names when you have them. Vague observations ("there's some misalignment") are worthless.
- If nothing is mismatched, say so plainly. Fabricating flags to fill a quota is worse than an empty list.
- Never invent evidence. Every claim must trace to something in the data blocks below.
- Keep each flag narrative tight — 2-4 sentences. No preamble.

The taxonomy block (stable, cached) and this outlet's state history + recent diagnostic excerpts follow."""


def _format_outlet_snapshot(outlet: Outlet, *, recent_limit: int = 20) -> str:
    """Outlet profile + recent state-change trajectory + recent diagnostic narrative."""
    lines: list[str] = []
    champ = outlet.data_champion.username if outlet.data_champion else "UNFILLED"
    lines.append(
        f"OUTLET: {outlet.name} (outlet_id={outlet.id}) · cohort {outlet.cohort or '—'} · data champion: {champ}"
    )

    # Recent state-change trajectory (most recent first, across all items)
    recent = list(
        outlet.states.select_related("item", "item__cluster", "set_by")
        .order_by("-set_at")[:recent_limit]
    )
    lines.append("")
    if recent:
        lines.append(f"Recent state changes (most recent first, up to {recent_limit}):")
        for s in recent:
            champ_str = " +champion" if s.led_by_champion else ""
            lines.append(
                f"  {s.set_at:%Y-%m-%d} · {s.item.cluster.name} / {s.item.name} "
                f"→ {s.get_level_display()}{champ_str}"
                f" — evidence: \"{s.evidence_excerpt}\""
            )
    else:
        lines.append("No state changes recorded for this outlet yet.")

    # Current state counts by level for orientation
    level_counts: dict[str, int] = {}
    latest: dict[int, CapabilityState] = {}
    for s in outlet.states.select_related("item").order_by("-set_at"):
        if s.item_id not in latest:
            latest[s.item_id] = s
    for s in latest.values():
        label = s.get_level_display()
        level_counts[label] = level_counts.get(label, 0) + 1
    champions = sum(1 for s in latest.values() if s.led_by_champion)
    if level_counts:
        lines.append("")
        lines.append(
            "Current depth distribution (counting only items with a recorded level): "
            + ", ".join(f"{k}={v}" for k, v in sorted(level_counts.items()))
            + f"; led-by-champion count={champions}"
        )

    # Last few diagnostics' narrative
    diagnostics = list(
        outlet.diagnostics.select_related("conducted_by").order_by("-date")[:3]
    )
    if diagnostics:
        lines.append("")
        lines.append("Recent diagnostic notes (most recent first):")
        for d in diagnostics:
            lines.append(
                f"\n--- {d.date:%Y-%m-%d} (by {d.conducted_by.username}) ---\n"
                f"{d.notes_raw.strip()}"
            )
    return "\n".join(lines)


def run_mismatch(outlet: Outlet, *, client=None) -> dict[str, Any]:
    if client is None:
        client = get_client()

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        thinking={"type": "adaptive"},
        output_config={"effort": EFFORT},
        system=[
            {"type": "text", "text": SYSTEM_PROMPT},
            {
                "type": "text",
                "text": _format_taxonomy(),
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": _format_outlet_snapshot(outlet),
                    },
                    {
                        "type": "text",
                        "text": (
                            "Report mismatches between stated priorities and "
                            "evidence. If there are none, say so plainly in the "
                            "headline and return an empty flags list. Comment on "
                            "bus-factor risk separately."
                        ),
                    },
                ],
            }
        ],
        tools=[TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": TOOL_NAME},
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        raise RuntimeError(
            f"Model returned no tool_use block. stop_reason={response.stop_reason}"
        )

    inp = tool_use.input
    usage = response.usage
    return {
        "headline": inp.get("headline", ""),
        "flags": list(inp.get("flags", [])),
        "bus_factor_risk": inp.get("bus_factor_risk", ""),
        "model": response.model,
        "stop_reason": response.stop_reason,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        },
    }
