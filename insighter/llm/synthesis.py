"""Diagnostic-note synthesis: Claude proposes capability state changes with evidence.

Two cacheable blocks:
  1. System: instruction + full taxonomy (stable across every request).
  2. First user block: outlet current state (stable per outlet).
Ephemeral: the raw diagnostic notes + per-call instruction.

Taxonomy serialization is deterministic — sorted by cluster.order, item.order —
so cache hits are predictable. Usage is returned alongside the parsed proposals
so callers can assert cache hits in tests or surface them in the UI.
"""
from __future__ import annotations

from typing import Any

from capabilities.models import CapabilityState, Cluster, Outlet
from diagnostics.models import Diagnostic
from insighter.llm.client import EFFORT, MAX_TOKENS, MODEL, get_client

TOOL_NAME = "propose_state_changes"

TOOL_SCHEMA: dict[str, Any] = {
    "name": TOOL_NAME,
    "description": (
        "Record proposed capability state changes derived from the diagnostic "
        "notes. Each proposal must cite verbatim evidence from the notes."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "proposals": {
                "type": "array",
                "description": (
                    "One entry per capability where the notes contain concrete "
                    "evidence of current state. Skip capabilities the notes "
                    "don't touch. An empty list is a valid answer."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "item_id": {
                            "type": "integer",
                            "description": "CapabilityItem primary key from the taxonomy block.",
                        },
                        "proposed_level": {
                            "type": "string",
                            "enum": ["Unknown", "Aware", "Practising", "Embedded"],
                            "description": (
                                "Depth of practice. Unknown only when the notes "
                                "refer to the item but give no clear signal."
                            ),
                        },
                        "led_by_champion": {
                            "type": "boolean",
                            "description": (
                                "True only if the notes indicate an outlet-side "
                                "data champion is sustaining this specific "
                                "capability without programme staff."
                            ),
                        },
                        "evidence_excerpt": {
                            "type": "string",
                            "description": (
                                "Verbatim quote from the notes that anchors the "
                                "proposal. Must be text that literally appears "
                                "in the notes."
                            ),
                        },
                        "confidence": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "1 = inferred / weak; 5 = explicit in notes.",
                        },
                        "rationale": {
                            "type": "string",
                            "description": (
                                "One sentence tying the evidence to the proposed "
                                "level."
                            ),
                        },
                    },
                    "required": [
                        "item_id",
                        "proposed_level",
                        "led_by_champion",
                        "evidence_excerpt",
                        "confidence",
                        "rationale",
                    ],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["proposals"],
        "additionalProperties": False,
    },
}

SYSTEM_PROMPT = """You assist specialists running audience-development diagnostic calls for independent newsrooms in a shared services hub.

Your job is narrow: read raw diagnostic call notes and propose capability state updates against the desk's fixed taxonomy. You do not give advice, make recommendations, or summarise the conversation.

Rules you must follow without exception:
- Only propose a state change when the notes contain concrete evidence of practice — something the outlet is actually doing, or a specific absence of practice. Aspiration, intent, and advice the specialist delivered do not count.
- Every evidence_excerpt must be a verbatim quote from the notes. Never paraphrase, never synthesise, never extend. If no verbatim quote supports a proposal, do not make the proposal.
- Prefer silence over thin evidence. Returning an empty proposals list is a valid answer when the notes don't warrant one.
- The level scale captures depth of practice only:
  * Aware — outlet knows the concept, no practice yet
  * Practising — some execution, inconsistent or early
  * Embedded — consistent, part of regular workflow
  * Unknown — notes refer to the item but give no clear signal to place a level
- led_by_champion is a separate dimension (bus-factor). Set it true only if the notes indicate an outlet-side data champion is sustaining this specific capability without programme staff. Most proposals will leave it false.
- Confidence: 1 = inferred / weak; 3 = implied across multiple sentences; 5 = explicit in the notes.
- Use the taxonomy item_ids exactly as listed. Never invent ids.

The two blocks that follow — taxonomy and outlet state — stay stable across calls. Use them for grounding; do not re-summarise them back to the user."""


def _format_taxonomy() -> str:
    """Deterministic taxonomy serialization for prompt caching.

    Order: cluster.order → item.order → item.name. Includes item metadata
    (priority, baseline, template-able, phase, assessment, cross-desk dep)
    and the L2 subcluster so the model can reason about grouping.
    """
    lines = [
        "TAXONOMY — audience-development capabilities.",
        "Use the item_id values verbatim when proposing state changes.",
        "",
    ]
    for cluster in Cluster.objects.prefetch_related("items").order_by("order", "name"):
        lines.append(f"## {cluster.order}. {cluster.name}")
        for item in cluster.items.order_by("order", "name"):
            meta_parts: list[str] = []
            if item.priority == "H":
                meta_parts.append("priority=High")
            elif item.priority == "L":
                meta_parts.append("priority=Low")
            else:
                meta_parts.append("priority=Medium")
            if item.baseline:
                meta_parts.append("baseline")
            if item.template_able:
                meta_parts.append("template-able")
            meta_parts.append(f"phase={item.get_phase_display()}")
            meta_parts.append(f"assessment={item.get_assessment_method_display()}")
            if item.cross_desk_dep:
                meta_parts.append(f"gated-by={item.cross_desk_dep}")
            subcluster = item.subcluster or "-"
            lines.append(
                f"  [item_id={item.id}] ({subcluster}) {item.name}"
            )
            lines.append(f"      meta: {', '.join(meta_parts)}")
            if item.description:
                description_one_line = " | ".join(
                    ln.strip() for ln in item.description.splitlines() if ln.strip()
                )
                lines.append(f"      description: {description_one_line}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _format_outlet_state(outlet: Outlet) -> str:
    """Current state per item (latest row wins). Ordered by item_id for determinism."""
    latest: dict[int, CapabilityState] = {}
    for state in outlet.states.select_related("item").order_by("-set_at"):
        if state.item_id not in latest:
            latest[state.item_id] = state

    header = (
        f"OUTLET STATE — {outlet.name} (outlet_id={outlet.id})\n"
        f"Cohort: {outlet.cohort or '—'} | "
        f"Data champion: {outlet.data_champion.username if outlet.data_champion else 'UNFILLED'}\n"
    )

    if not latest:
        return header + "No capability state recorded yet for this outlet."

    lines = [header, "Current capability state per item (only items with recorded state are listed):"]
    for state in sorted(latest.values(), key=lambda s: s.item_id):
        champ = " · led-by-champion" if state.led_by_champion else ""
        lines.append(
            f"  item_id={state.item_id} → {state.get_level_display()}{champ} "
            f"(set {state.set_at:%Y-%m-%d} by {state.set_by.username})"
        )
    return "\n".join(lines)


def _format_notes_block(diagnostic: Diagnostic) -> str:
    return (
        f"DIAGNOSTIC\n"
        f"Date: {diagnostic.date:%Y-%m-%d}\n"
        f"Conducted by: {diagnostic.conducted_by.username}\n\n"
        f"Raw notes:\n"
        f"---\n{diagnostic.notes_raw}\n---\n\n"
        f"Propose state changes for any capabilities the notes cover. "
        f"Return an empty proposals list if the notes don't contain concrete "
        f"evidence of practice."
    )


def run_synthesis(diagnostic: Diagnostic, *, client=None) -> dict[str, Any]:
    """Call Claude with the diagnostic's raw notes; return parsed proposals + usage.

    Pass `client` to inject a test double; otherwise a live Anthropic client is
    built from env.
    """
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
                        "text": _format_outlet_state(diagnostic.outlet),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {"type": "text", "text": _format_notes_block(diagnostic)},
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

    usage = response.usage
    return {
        "proposals": list(tool_use.input.get("proposals", [])),
        "model": response.model,
        "stop_reason": response.stop_reason,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        },
    }
