# Insighter — status after Thursday resume

## What changed this session

Three things shipped; one blocked on your call.

| # | Task | Outcome | Commit |
|---|------|---------|--------|
| 1 | Split level scale (depth vs bus-factor) | ✅ done | `942a337` |
| 2 | Add MIT LICENSE | ✅ done | `6bb941f` |
| 3 | Backfill taxonomy metadata from xlsx | ⛔ blocked on schema decision | — |
| 4 | Update STATUS + DECISIONS | ✅ done | this commit |

## Blocker — taxonomy granularity

The xlsx metadata is at **L3 task** level (90 tasks), our model maps
`CapabilityItem` to **L2 subcluster** (43 items). Metadata varies within
L2 groups for most fields — lossless aggregation isn't available.

See **DECISIONS.md #7** for the full breakdown and 4 options. Recommended
option is (a): rebuild fixture as L3 tasks. Default on next resume
unless you pick otherwise.

## Test state

9 tests passing (added one for the champion flag being independent of
depth).

## Git state

```
6bb941f Add MIT LICENSE
942a337 Split level scale: separate depth from bus-factor
db62a70 Add STATUS.md summarising overnight execution stop
51c08c8 Build outlet detail + state-change + diagnostic-entry flows
ec676e0 Seed audience-development taxonomy from brief
4828a37 Define core data model for capability tracker
ab14d2a Scaffold Django 5 project with capabilities + diagnostics apps
```

`main` is 2 commits ahead of `origin/main` (you rewrote the earlier
bad commit out, so history is clean — no xlsx blob anywhere).

## Pending (unchanged)

- **Friday** (requires your input on prompts + API key): Anthropic SDK,
  synthesis endpoint, mismatch flagger, diff UI
- **Saturday**: "why stuck" view, sponsor matcher, stubs, read-only
  taxonomy browser, first demo video
- **Sunday**: README, deploy doc, final video, summary, buffer

## What I did not touch

Per overnight rules:
- No LLM integration code.
- No seed outlet or diagnostic content.
- No demo UX polish.
- No schema rebuild for the L3-task question — waiting for your call.

## Time budget

~30 min wall-clock this session. 2 commits landed (+ 1 to wrap now).
Hard stop cap of 5 not hit.
