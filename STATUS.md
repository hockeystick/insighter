# Insighter — status

## This session

| Commit    | What                                                     |
|-----------|----------------------------------------------------------|
| `942a337` | Split level scale (depth vs bus-factor)                  |
| `6bb941f` | Add MIT LICENSE                                          |
| `52aca24` | Update STATUS + DECISIONS mid-session                    |
| `84f523c` | Rebuild taxonomy fixture from L3 tasks                   |
| *this*    | Close out DECISIONS after #7 resolved                    |

## Current state

- **Data model**: unchanged since the earlier schema. `CapabilityState`
  now has `led_by_champion: bool` distinct from `level` (depth).
- **Taxonomy**: 12 clusters × 90 items loaded from the desk xlsx, with
  full metadata per item. L2 subcluster is encoded in `description`.
- **Tests**: 9 passing.
- **Git**: `main` is 5 commits ahead of `origin/main`. Clean history —
  no xlsx blobs in any commit.

## How to reload taxonomy from scratch

```bash
# xlsx must be present at the project root, gitignored
.venv/bin/python scripts/build_taxonomy_fixture.py
.venv/bin/python manage.py shell -c "
from capabilities.models import Cluster, CapabilityItem, CapabilityState
CapabilityState.objects.all().delete()
CapabilityItem.objects.all().delete()
Cluster.objects.all().delete()
"
.venv/bin/python manage.py loaddata taxonomy_seed
```

## Decisions resolved this session

- #1 level scale → split
- #2 license → MIT
- #3 taxonomy metadata → backfilled from xlsx (part of #7)
- #7 taxonomy granularity → option (a), L3 tasks are items

## Decisions still pending

- #4 mismatch flagger prompt (Friday)
- #5 seed outlet voices + diagnostic notes (you)
- #6 demo UX polish (Saturday)

## Pending work

- **Friday**: Anthropic SDK wrapper + prompt caching, synthesis
  tool-use endpoint, mismatch flagger endpoint, diff UI for
  reviewing proposed state changes.
- **Saturday**: "why is this outlet stuck" composed view, sponsor
  matcher filtered table, stub screens for Specialist deployment +
  CheckIn with seed data, read-only taxonomy browser (not admin),
  first demo video cut.
- **Sunday**: README + deploy doc, written summary, final demo
  video re-record, buffer.

## What I did not touch

- No LLM integration.
- No seed outlet / diagnostic content.
- No demo UX polish.
- No schema changes beyond the `0003_capabilitystate_led_by_champion` migration.

## Time budget

~45 min wall-clock this session. 5 commits landed. Hard stop cap hit
cleanly at the end of the L3-fixture work, as intended.
