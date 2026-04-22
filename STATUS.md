# Insighter — overnight status

Stop triggered at the end of Thursday's scope (per your rules: no LLM
work overnight; 5-commit / 4-hour cap observed).

## What's done

**4 commits** on `main`:

1. `ab14d2a` Scaffold Django 5 project with capabilities + diagnostics apps
2. `4828a37` Define core data model for capability tracker
3. `ec676e0` Seed audience-development taxonomy from brief
4. `51c08c8` Build outlet detail + state-change + diagnostic-entry flows

**Working v0.1 flow** (all green on `manage.py test` — 8 passing):
- Outlet list → outlet detail → capability state grid by cluster
- Manual state-change form (appends a row; history never mutated)
- Diagnostic entry (raw notes textarea → detail view with linked state changes)
- Login-required on all app views; Django admin at `/admin/` for
  taxonomy maintenance
- Tailwind via CDN, no build step

**Taxonomy seeded**: 9 clusters × 43 items, names verbatim from the
brief. Metadata fields at model defaults pending your pass.

**Tests**: append-only semantics, evidence-required validation, view
smoke tests (list / detail / state append / diagnostic redirect /
login-required redirect).

## How to run it

```bash
cd /Users/alimahmood/Downloads/Insighter
.venv/bin/python manage.py createsuperuser     # one-time
.venv/bin/python manage.py loaddata taxonomy_seed
.venv/bin/python manage.py runserver
```
Then: http://127.0.0.1:8000/admin/ to add an Outlet, then
http://127.0.0.1:8000/ for the tracker view.

## What's pending your input (see DECISIONS.md)

1. **Level scale** — single field conflates depth with bus-factor;
   options a/b/c listed. Default = keep single field.
2. **License** — AGPL-3.0 vs MIT; no `LICENSE` written yet.
3. **Taxonomy metadata values** — 43 items need priority / baseline /
   template-able / phase / assessment-method / cross-desk-dep set per
   your judgment.
4. **Mismatch flagger prompt** — Friday scope, waiting on you.
5. **Seed outlet voices + diagnostic notes** — Plan-review called this
   out as the highest-leverage Thursday task. `fixtures/demo_outlets.json`
   is empty.
6. **Demo UX polish** — colour choices, grid layout beyond basic,
   typography. Saturday scope, your call.

## Pending tasks

- **Friday** (requires your inputs on prompts + API key):
  - Anthropic SDK wrapper with prompt caching on taxonomy block
  - Synthesis tool-use endpoint (schema done per plan; prompt TBD)
  - Mismatch flagger endpoint (same)
  - Diff UI for reviewing proposed state changes
- **Saturday**:
  - "Why is this outlet stuck?" composed view (Plan-review addition)
  - Sponsor matcher filtered table
  - Stub screens for Specialist deployment + CheckIn with seed data
  - Read-only taxonomy browser (not admin) for the demo
  - First demo-video cut
- **Sunday**:
  - README + LICENSE + deploy doc
  - Written summary
  - Final demo video re-record
  - Buffer

## What I did not touch

Per overnight rules:
- No LLM integration code, no `anthropic` dependency, no API key usage.
- No seed outlet or diagnostic-note content written.
- No level-scale schema split (DECISIONS.md #1 unresolved).
- No license file.
- No UX beyond basic server-rendered Tailwind layout.

## Risks / things to verify when you're back

- Migrations: 3 applied (`capabilities.0001`, `diagnostics.0001`,
  `capabilities.0002`). If you change the level-scale schema, squash
  these before the fixture gets filled in — cheaper now than later.
- Tailwind-via-CDN is fine for dev but judges may probe offline demos.
  Worth a 5-min `pip install django-tailwind` swap Saturday if demo
  needs to run air-gapped.
- `login_required` points to `/admin/login/` — fine for v0.1, but flag
  in README that this is staff-only and the high-risk-env access
  control story is v0.2.

## Time budget used

Roughly 2 hours wall-clock. 4-hour / 5-commit cap not hit.
