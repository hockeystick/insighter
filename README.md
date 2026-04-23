# Insighter

A capability state tracker for shared services newsroom hubs — built
during the Opus 4.7 × Claude Code hackathon (Apr 22–26 2026).

## The problem

Shared services hubs match three sides of a marketplace — outlets,
specialists, sponsors — to move independent newsrooms through structured
capability development. At 10 outlets the matching fits in human heads.
Past 50, it doesn't. The fix isn't a task tracker; it's a **live record
of capability state** anchored to a shared taxonomy, where the signal
comes from diagnostic conversations rather than outlet self-report.

## What's in v0.1

- **Capability state tracker** for an audience development service desk.
  12 clusters, 90 capabilities, per-item metadata (priority, baseline,
  template-ability, phase, assessment method, cross-desk dependency).
- **Append-only state history** per (outlet, capability). Current state
  = most recent row. Every state change carries required evidence.
- **Depth × bus-factor split**: `level` captures how deeply the practice
  has landed (Unknown / Aware / Practising / Embedded). A separate
  `led_by_champion` flag captures whether an outlet-side data champion
  is sustaining it — honest to the "Bus Factor > 1" KPI.
- **Diagnostic-first workflow**: paste raw call notes, attach state
  changes to a diagnostic, preserve evidence excerpts.
- **Read-only taxonomy browser** at `/taxonomy/` for demos and onboarding
  without exposing the admin UI.
- **Django admin** for non-coder taxonomy maintenance.

## What's coming (hackathon roadmap)

- **Opus 4.7 synthesis**: paste a diagnostic call's raw notes → model
  proposes structured state changes with evidence excerpts, reviewer
  diffs and accepts. Tool-use with prompt caching on the taxonomy.
- **Mismatch flagger**: cross-reference outlet's stated priorities
  against recent state changes, surface drift.
- **"Why is this outlet stuck?"** — a single composed view combining
  state, recent diagnostics, bus-factor, and the mismatch flag.
- **Sponsor matcher**: tag outlets, specialists, and sponsors on the
  same dimensions (region, language, format, topic) so routing doesn't
  require human re-analysis.
- **Specialist deployment ledger** and **30/60/90 behavioural check-ins**:
  schema present, UI stubbed; full flows post-hackathon.

## Stack

- Django 5, SQLite, HTMX-ready (no JS build step)
- Tailwind via CDN
- `anthropic` SDK with prompt caching for the model calls (coming)

Chosen for: ships fast on a deadline, Django admin gives non-coders
taxonomy editing for free, no managed services needed for self-hosting.
Rejected Next.js + Supabase (self-host story is heavy), FastAPI + custom
admin (rebuilding Django admin wastes a day).

## Running it locally

Requires Python 3.11+.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py loaddata taxonomy_seed
.venv/bin/python manage.py runserver
```

Then:
- `http://127.0.0.1:8000/taxonomy/` — public read-only taxonomy browser
- `http://127.0.0.1:8000/admin/` — add an Outlet (and log in)
- `http://127.0.0.1:8000/` — outlet list → detail view

Tests:
```bash
.venv/bin/python manage.py test
```

## Rebuilding the taxonomy from source

The taxonomy fixture is generated from the desk's internal xlsx (not
committed). If you have the xlsx:

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python scripts/build_taxonomy_fixture.py
```

Reload into an existing DB:
```bash
.venv/bin/python manage.py shell -c "
from capabilities.models import Cluster, CapabilityItem, CapabilityState
CapabilityState.objects.all().delete()
CapabilityItem.objects.all().delete()
Cluster.objects.all().delete()
"
.venv/bin/python manage.py loaddata taxonomy_seed
```

## Security posture

v0.1 is **staff-only, single-tenant**. Authenticated views require
Django login. Audit trail comes from the append-only `CapabilityState`
log. Access controls appropriate for high-risk-environment users
(2FA, granular per-outlet permissions, field-level redaction) are
**v0.2 scope** — do not deploy v0.1 as-is in those contexts.

## Project conventions

- The diagnostic conversation is the source of truth. Data structure
  exists to support it, not replace it.
- State changes require evidence excerpts — no empty rows.
- Claude/Opus 4.7 is used where semantic reading against structured
  state adds judgment a template can't: diagnostic synthesis and
  mismatch flagging. Not as a wrapped chat box.
- Everything reproducible: fixtures from the xlsx, DB from migrations,
  no hand-edited binary state.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgements

Built by Ali Mahmood during the Opus 4.7 hackathon. The audience
development taxonomy is the working document of the service desk at
[the hub]; reproduced here with permission.
