# Demo script — 3-minute submission recording

Target: 3:00. Cut ruthlessly to keep under 3:10. Don't narrate what's on screen that the viewer can read — narrate what it means.

## Pre-roll setup (do before you hit record)

- [ ] Fresh Chrome/Safari profile, zoom 110%
- [ ] Tabs preloaded:
  - [ ] `http://127.0.0.1:8000/` — outlet list
  - [ ] `http://127.0.0.1:8000/outlet/<your-seed-outlet>/` — outlet detail (pick the outlet where synthesis will land most of its proposals)
  - [ ] `http://127.0.0.1:8000/diagnostics/<diagnostic-id>/` — diagnostic page for that outlet (notes pre-pasted, synthesis NOT yet run — you'll run it live)
  - [ ] `http://127.0.0.1:8000/outlet/<your-seed-outlet>/why-stuck/` — pre-compute the mismatch flag before recording so it renders instantly. The cached output still shows real cache-read tokens.
  - [ ] `http://127.0.0.1:8000/match/sponsor/<meridian-or-similar>/` — a sponsor with at least one overlapping outlet
- [ ] Terminal with `.venv/bin/python manage.py runserver` visible so judges see it's local
- [ ] `ANTHROPIC_API_KEY` confirmed exported in the server's shell

## Beat-by-beat

### 0:00–0:20 — Problem (voice over outlet list)
- [ ] Open on the outlet list page.
- [ ] "Shared services hubs for independent newsrooms need to keep outlets, specialists, and sponsors matched as outlets move through capability development. At ten outlets this fits in one person's head. At fifty it doesn't — matching gets redone in every diagnostic call."
- [ ] "Insighter is a live record of capability state anchored to the desk's working taxonomy. Built this week with Opus 4.7 and Claude Code."

### 0:20–0:50 — Tracker (outlet detail)
- [ ] Click into your pre-picked outlet.
- [ ] "Each outlet has a live state record against 90 capabilities across 12 clusters. State changes carry the evidence that anchored them."
- [ ] Hover one badge: "the level is depth of practice." Point to a champion badge: "the green marker is a separate bus-factor flag — is an outlet-side data champion sustaining this capability without programme staff?"
- [ ] Click into the history: "every state change is append-only, with a verbatim evidence excerpt."

### 0:50–2:00 — Synthesis (the visual centrepiece)
- [ ] Jump to the prepared diagnostic page. "Today's diagnostic — raw notes from the call."
- [ ] Click **Run synthesis**. "Claude Opus 4.7 reads the notes against the full taxonomy and our current state for this outlet. The taxonomy is cached — look at the cache-read tokens at the top of the review page."
- [ ] Review page loads. Point at the cache-read counter: "7K tokens served from cache — the taxonomy block doesn't re-bill."
- [ ] Walk through 2–3 proposals: "each one has a verbatim evidence excerpt, a confidence score, and a rationale. The system prompt forbids paraphrasing evidence — these are literal quotes."
- [ ] Tick accept on 5, tick reject on one (say why: "this one's aspirational, not practice"), edit the level on one ("the notes actually show this further along").
- [ ] Click **Apply accepted proposals**. Land back on the outlet. State grid has updated. "Each accepted proposal appends a new state row with `llm_proposed=true` and my user as the reviewer — the append-only history preserves that the model drafted and I accepted."

### 2:00–2:30 — Mismatch flag (the Opus 4.7 argument)
- [ ] Click **Why stuck?** → the why-stuck page renders the pre-computed mismatch flag.
- [ ] Read the headline.
- [ ] "This is cross-referential: the model is reading stated priorities from diagnostic narrative against the evidence trail of what's actually moved. That's the judgment a template can't do."
- [ ] Point at bus-factor indicators: "these are deterministic — data champion presence, state-change cadence, embedded count. The mismatch flagger narrates what that data means in context."

### 2:30–2:50 — Shared data layer
- [ ] Jump to sponsor match page for one of your sponsors.
- [ ] "Outlets, specialists, and sponsors share a single tag vocabulary — region, language, format, topic. No separate sponsor CRM. Routing collapses to a tag-set intersection."
- [ ] Flash deployments + check-ins list views briefly: "same data layer powers specialist deployment and 30/60/90 behavioural check-ins. These ship full in v0.2."

### 2:50–3:00 — Close
- [ ] "Everything open source, MIT, self-hostable. Django admin gives non-coder taxonomy maintenance for free. Built from scratch this week."
- [ ] End on the repo URL.

## Common rehearsal mistakes

- **Don't open the Django admin on camera.** The taxonomy browser (`/taxonomy/`) is the read-only version meant for demos.
- **Don't live-run the mismatch flagger** unless you're confident latency is under 15s — it's 10–30s depending on load. Pre-compute and re-render; the cache-read tokens on the page are real either way.
- **Do not narrate the screen**. "Here's the outlet page" adds nothing — judges can see. Say what it means.
- **Stopwatch, not vibes.** Dry-run twice with a timer before recording. 3:30 is long.

## After recording

- [ ] Confirm video has no audio drift
- [ ] Upload to whatever the hackathon specifies (unlisted YouTube / S3 / etc.)
- [ ] Link it from the README above the Acknowledgements section
