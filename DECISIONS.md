# Decisions pending — need your input

Logged during overnight execution. Each item is paused per the overnight
rules; nothing here has been guessed in code.

## 1. Level scale: does `level` conflate depth with bus-factor?

**Current plan**: single `level` field on `CapabilityState` with values
`Unknown / 1 Aware / 2 Practising / 3 Embedded / 4 Data-champion-led`.

**The tension**: level 4 ("data-champion-led") encodes *who is sustaining
the practice*, while levels 1–3 encode *how deeply the practice has
landed*. An outlet could be at "embedded" depth but still dependent on
programme staff (bus factor = 1), or at "practising" depth but already
self-sustaining on that specific capability.

**Options**:
- (a) Keep single `level` as-is. Simpler; demo reads cleaner; the
  conflation is a known limitation.
- (b) Split into two fields: `depth` (1–4) + `sustained_internally`
  (bool, nullable). More honest to the Bus-Factor KPI. One more column
  in the state grid UI.
- (c) Split into `depth` (1–4) + `ownership` (enum:
  `programme-dependent / shared / outlet-led`). Most expressive;
  heaviest UI.

**Implemented now**: option (a) scaffolded with a comment in the model.
Migration is trivial to change if you pick (b) or (c) before Friday.

**Question for you**: (a), (b), or (c)? Default if no answer by Thursday
evening = (a).

## 2. License: AGPL-3.0 vs MIT?

**Plan draft said AGPL-3.0**. Reasoning was "open source end to end"
+ "self-hostable" implies protecting the hub's work from being
re-hosted as a closed SaaS.

**Counter-argument for MIT**: maximum reuse by other newsrooms and
desks, less friction for sponsors/partners adopting the code, better
ecosystem fit for hackathons.

**Not implemented**: no `LICENSE` file written yet. Please pick.
Default if no answer = AGPL-3.0 per the plan.

## 3. Taxonomy metadata values per item

The brief listed the 9 clusters and their items by name, but didn't
specify the per-item metadata values (priority H/M/L, baseline y/n,
template-able y/n, phase, assessment method, cross-desk dependency).

**Implemented**: fixture with cluster + item names only. Metadata
fields set to neutral defaults (priority=Medium, baseline=False,
template_able=False, phase=Advisory, assessment_method=Interview,
cross_desk_dep=null). These are placeholders, **not** judgments.

**Needed from you**: a pass through `fixtures/taxonomy_seed.json`
to fill in the real metadata values, or a separate spreadsheet I can
convert. Roughly 45 items × 6 fields.

## 4. Mismatch flagger prompt wording

Scoped out of overnight per your rules. Endpoint + tool schema will
be scaffolded Friday; the actual system prompt wording waits for you.

## 5. Seed outlet voices + diagnostic note wording

Scoped out of overnight per your rules. `fixtures/demo_outlets.json`
and `fixtures/demo_diagnostics.json` left as empty JSON arrays with
TODO comments. Plan-review flagged this as the single highest-leverage
Thursday task — your voice, not mine.

## 6. UX decisions beyond basic layout

None taken overnight. Basic server-rendered tables + a capability
grid are scaffolded without Tailwind polish, colour choices, or demo
styling. Sat polish pass is yours to drive.
