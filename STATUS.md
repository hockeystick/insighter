# Insighter — demo-ready status

## Submission checklist

- [x] Capability state tracker (real)
- [x] Depth / bus-factor split on state (`level` + `led_by_champion`)
- [x] Append-only state history with required evidence excerpts
- [x] Diagnostic-note synthesis via Claude Opus 4.7 (tool-use, not chat)
- [x] Prompt caching on the ~7.7K-token taxonomy block
- [x] Review-diff UI: accept / edit / reject per proposal
- [x] Intent-vs-evidence mismatch flagger (Opus 4.7), cached on outlet
- [x] "Why is this outlet stuck" composed view
- [x] Sponsor matcher ranking outlets + specialists by SharedTag overlap
- [x] Deployment + check-in stub list views with empty states
- [x] Read-only taxonomy browser (public — not `/admin/`)
- [x] Django admin for non-coder taxonomy maintenance
- [x] MIT LICENSE
- [x] README, DEPLOY.md, DEMO.md
- [x] Dockerfile + docker-compose.yml (one-command self-host)
- [x] 24 tests passing (synthesis flow fully mocked; no network)
- [x] Pushed to `origin/main` on `hockeystick/insighter`
- [ ] Seed outlet content (yours — `fixtures/demo_outlets.example.json` is the template)
- [ ] Record the 3-min demo video (DEMO.md)
- [ ] Final submission form with repo URL + video link

## Git state

```
caa45dc  Add Docker Compose self-host, 3-min demo script, and outlet seed template
91d3f30  Sponsor matcher, deployment + check-in stubs, seeded reference data
fb7d7b8  Build mismatch flagger + 'why is this outlet stuck' composed view
27cef68  Build diagnostic-note synthesis on Claude Opus 4.7 (tool-use + caching)
a15d6e7  Add README
57bec2c  Group grid by L2 subcluster and add read-only taxonomy browser
84f523c  Rebuild taxonomy fixture from L3 tasks in the xlsx
6bb941f  Add MIT LICENSE
942a337  Split level scale: separate depth from bus-factor
```

All pushed to origin. `main` = HEAD.

## What's live in the app

| Path | What |
|---|---|
| `/` | Outlet list |
| `/outlet/<slug>/` | Outlet detail — capability grid grouped by cluster × subcluster, 90 items |
| `/outlet/<slug>/state/new/` | Manual state-change entry |
| `/outlet/<slug>/why-stuck/` | Composed impact-anchor view + mismatch flag |
| `/outlet/<slug>/mismatch/run/` | POST — runs the LLM mismatch flagger |
| `/diagnostics/outlet/<slug>/new/` | Log a diagnostic |
| `/diagnostics/<pk>/` | Diagnostic detail — Run Synthesis button lives here |
| `/diagnostics/<pk>/synthesis/run/` | POST — runs Claude Opus 4.7 synthesis |
| `/diagnostics/<pk>/synthesis/review/` | Review-diff UI (accept / edit / reject) |
| `/diagnostics/<pk>/synthesis/accept/` | POST — appends CapabilityState rows |
| `/match/` | Sponsor index (seeded with 4 sponsors) |
| `/match/sponsor/<pk>/` | Per-sponsor outlet + specialist ranking by tag overlap |
| `/deployments/` | Deployment stub list |
| `/checkins/` | Check-in stub list |
| `/taxonomy/` | Public read-only taxonomy browser |
| `/admin/` | Django admin — taxonomy + outlet maintenance |

## Claude Opus 4.7 integration surface

- Model `claude-opus-4-7`, adaptive thinking, effort `xhigh`, max_tokens 8192
- **Synthesis** (`insighter/llm/synthesis.py`): tool-use with
  `propose_state_changes`, schema enforces verbatim evidence excerpts,
  confidence 1–5, level enum. System prompt's verbatim-only rule means
  hallucinated evidence is structurally blocked.
- **Mismatch** (`insighter/llm/mismatch.py`): tool-use with
  `report_mismatches`, returns {headline, flags[{title, narrative,
  severity}], bus_factor_risk}.
- Prompt-cached taxonomy block (~7.7K tokens, > 4096 Opus 4.7 cache floor)
  + per-outlet state block. Both calls reuse the taxonomy cache within the
  5-minute TTL.
- Usage (cache-read, cache-write, model ID) surfaced inline on the review
  page and why-stuck page so judges can see the caching working during
  the demo.

## To record the demo

1. Write your three seed outlets by editing
   `fixtures/demo_outlets.example.json` → rename to
   `fixtures/demo_outlets.json` → `loaddata demo_outlets`.
2. Log a diagnostic for each outlet via the UI or admin, with realistic
   raw notes in your voice.
3. Pre-run the mismatch flagger on your hero outlet so the why-stuck
   page renders cached.
4. Follow `DEMO.md` beat-by-beat. Dry-run twice with a timer.

## Known limitations (v0.1 → v0.2)

- Staff-only auth; no per-outlet permissions, 2FA, or audit log beyond
  the append-only `CapabilityState` table.
- `DEBUG=1` in both native and Compose configs; not production-safe.
- Deployment and CheckIn screens are stubs — schema wired, UX for
  scheduling and response capture is v0.2 scope.
- Fast Mode / alternate models not plumbed; demo locks to Opus 4.7.
