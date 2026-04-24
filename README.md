# Insighter

**Status: archived.** A hackathon exploration that reached a working prototype
and then stopped. Not submitted, no demo video, no further development
planned. This repo is kept as a reference for the approach, not as active
software.

Built during the Claude Opus 4.7 × Claude Code hackathon (April 2026).

---

## What it was

A capability state tracker for shared services newsroom hubs — a marketplace
where three sides (outlets, specialists, sponsors) need to stay in sync as
outlets move through a structured capability development programme. Today
that matching happens in human heads during diagnostic calls. That fits at
ten outlets; it breaks past fifty.

The idea: make the desk's existing capability taxonomy a live, per-outlet
state store, anchored to diagnostic-conversation evidence, with Claude
Opus 4.7 reading raw call notes against the taxonomy to propose state
changes that a specialist reviews and accepts.

## What's in the code

Enough to demonstrate the approach end-to-end on a developer's machine:

- **Capability state tracker.** Django 5 + SQLite + HTMX-ready templates.
  12 clusters, 90 capabilities (sourced from an internal desk xlsx, not
  committed).
- **Append-only state history.** Every state change on every capability is
  a new row with a required evidence excerpt, timestamp, and author.
- **Depth × bus-factor split.** `level` (Unknown / Aware / Practising /
  Embedded) is depth of practice; a separate `led_by_champion` flag
  captures whether an outlet-side data champion is sustaining the
  capability. The two vary independently.
- **Claude Opus 4.7 synthesis** (`insighter/llm/synthesis.py`). Tool-use
  request with prompt caching on the taxonomy block and outlet-state
  block. Model returns proposed state changes with verbatim evidence
  excerpts; reviewer accepts / edits / rejects per proposal in a diff UI.
- **Intent-vs-evidence mismatch flagger** (`insighter/llm/mismatch.py`).
  Cross-references outlet's stated priorities (from diagnostic narrative)
  against the trajectory of recent state changes; returns narrative flags.
  Cached on the outlet so the view renders instantly.
- **"Why is this outlet stuck?" composed view.** Single screen combining
  the mismatch flag, bus-factor indicators, per-cluster level rollup, and
  recent trajectory.
- **Sponsor matcher.** Sponsors, outlets, and specialists share one
  SharedTag vocabulary (region, language, format, topic). Matching is
  tag-set intersection — no LLM.
- **Read-only taxonomy browser** at `/taxonomy/` for use in place of
  Django admin on camera.
- **Docker Compose self-host**, seed commands for sponsors / specialists /
  tags and for throwaway stub outlets, and 24 passing tests (LLM flows
  fully mocked in tests; no network calls).

## What's not there

- No demo video, no submission
- The user's three real seed outlets were never written — only the
  throwaway `seed_stub_outlets` command has concrete outlet data
- Deployment ledger and 30/60/90 behavioural check-in screens are stubs
  (schema wired, UX for scheduling and response capture not built)
- Production-grade auth posture (see DEPLOY.md § Security posture)

## Running it locally

Requires Python 3.11+ and an Anthropic API key for the LLM flows.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py loaddata taxonomy_seed
.venv/bin/python manage.py seed_demo_refs        # sponsors + specialists + tags
.venv/bin/python manage.py seed_stub_outlets     # 3 placeholder outlets for exercising the flows
export ANTHROPIC_API_KEY=sk-ant-...
.venv/bin/python manage.py runserver
```

Then:
- `http://127.0.0.1:8000/taxonomy/` — public read-only taxonomy browser
- `http://127.0.0.1:8000/admin/` — admin
- `http://127.0.0.1:8000/` — outlet list → detail → synthesis

Tests: `.venv/bin/python manage.py test` (nothing hits the network).

Docker Compose path is in [DEPLOY.md](DEPLOY.md).

## Decisions, architecture notes

See [DECISIONS.md](DECISIONS.md) for the design decisions that landed
(level-scale split, license choice, taxonomy granularity, synthesis +
mismatch prompt rule-sets) and small architectural notes — L2 subcluster
is parsed from `description` rather than modelled, the taxonomy fixture
is generated from an xlsx that's intentionally gitignored, prompt cache
hits depend on deterministic serialization.

## License

MIT — see [LICENSE](LICENSE).
