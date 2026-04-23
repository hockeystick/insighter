# Decisions log

## Resolved

| # | Decision | Outcome | Commit |
|---|----------|---------|--------|
| 1 | Level scale — conflates depth and bus-factor? | **Split.** `level` enum (Unknown / Aware / Practising / Embedded) is depth only; `led_by_champion` bool carries bus-factor. | `942a337` |
| 2 | License — AGPL-3.0 vs MIT | **MIT.** | `6bb941f` |
| 3 | Taxonomy metadata values per item | **Backfilled from the desk xlsx** (L3-task granularity) as part of #7. | `84f523c` |
| 4 | Mismatch flagger prompt wording | **Written in `insighter/llm/mismatch.py`.** System prompt is narrow: report gaps between stated priorities and evidence trail, cite clusters / item names, prefer empty flags over fabrication. Iterate against real seed data. | `fb7d7b8` |
| 5 | Seed outlet voices + diagnostic notes | **User-owned.** `fixtures/demo_outlets.example.json` is the schema template. | — |
| 6 | Demo UX polish | **Shipped functional** — subcluster grouping on the state grid, severity-coloured mismatch flags, cache-read token counters inline, dedicated why-stuck Impact-anchor page. More polish is yours. | `57bec2c`, `fb7d7b8` |
| 7 | Taxonomy granularity — L2 vs L3 | **L3 (tasks) become CapabilityItems.** 90 items across 12 clusters. | `84f523c` |

## Synthesis prompt — the rule-set I committed to

All in `insighter/llm/synthesis.py` SYSTEM_PROMPT. Rewritable before the
demo if you want to tune, but the shape matters:

- Read raw diagnostic notes against the fixed taxonomy; do not advise.
- Only propose a state change with concrete evidence of practice —
  aspiration and advice delivered don't count.
- Evidence must be verbatim quotes. No paraphrase.
- Empty proposals list is a valid answer.
- Level scale is depth only (Aware → Practising → Embedded + Unknown).
- `led_by_champion` is separate and usually false.
- Confidence 1–5 (inferred → explicit).

## Mismatch prompt — the rule-set I committed to

All in `insighter/llm/mismatch.py` SYSTEM_PROMPT:

- Stated priorities come from diagnostic narrative; evidence comes
  from state-change trajectory + data-champion presence.
- A mismatch is a contradiction or drag in direction, not a level bar.
- Cite cluster or item names; vague flags are worthless.
- If nothing is mismatched, say so plainly. Empty flags list is
  preferable to fabricated ones.
- Bus-factor gets its own field so it doesn't compete with the
  mismatch flags.

## Small architectural notes worth keeping

- **L2 subcluster is not a first-class field.** Parsed from the
  `description` prefix via `CapabilityItem.subcluster` property. If you
  ever want queryable subcluster (e.g. for dedicated subcluster pages),
  add a `subcluster: CharField` + re-run the ingest script — no state
  data migration needed.
- **Taxonomy fixture is generated from the xlsx, not hand-edited.**
  `scripts/build_taxonomy_fixture.py` is the source of truth for how
  xlsx rows map into CapabilityItem fields. Re-run it whenever the
  xlsx changes.
- **xlsx is gitignored.** `.gitignore` excludes `*.xlsx` + the
  Plus-Hub filename prefix. Don't commit it.
- **Prompt cache hits depend on deterministic serialization.** Tests
  cover that `_format_taxonomy()` is byte-stable across calls — don't
  accidentally introduce dict iteration or time-based interpolation.
- **Outlet.mismatch_flag_json is a cache, not the source of truth.**
  Running the mismatch flagger overwrites it. The button is prominent
  on the why-stuck page.
- **No tests hit the Anthropic API.** Synthesis + mismatch flows are
  mocked in `diagnostics/tests.py`. If you add a live smoke test,
  gate it on `ANTHROPIC_API_KEY` and keep it out of `manage.py test`.
