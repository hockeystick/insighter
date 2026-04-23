# Decisions log

## Resolved

- **#1 Level scale**: split. `level` enum is now Unknown / Aware / Practising /
  Embedded (depth only); `led_by_champion: bool` is a separate field for
  bus-factor-at-capability. Migration `capabilities.0003`. Commit `942a337`.
- **#2 License**: MIT. `LICENSE` committed (`6bb941f`).
- **#7 Taxonomy granularity**: option (a), L3 tasks become CapabilityItems.
  Fixture rebuilt from the xlsx: 12 clusters × 90 items with real
  per-item metadata. L2 subcluster preserved in the `description` field.
  Ingest script at `scripts/build_taxonomy_fixture.py` is reproducible
  from the xlsx. Commit `84f523c`.
- **#3 Taxonomy metadata values**: backfilled as part of #7 — Priority /
  Baseline / Template-able / Phase / Assessment / Cross-desk-dep are all
  populated from the xlsx on every item (with model defaults for the 7
  blank rows).

## Still pending

- **#4 Mismatch flagger prompt**: Friday scope, waiting on you.
- **#5 Seed outlet voices + diagnostic notes**: yours to write — Plan-review
  flagged this as the highest-leverage Thursday task.
- **#6 Demo UX polish**: Saturday scope.

## Implementation notes worth keeping

- L2 subcluster is not a first-class field. If you want the outlet detail
  page to group items by subcluster instead of just cluster, the cheapest
  path is adding a `subcluster: CharField` to `CapabilityItem` and
  re-running the ingest script — no migration of existing state rows
  needed since state rows are keyed by item, not by subcluster.
- The xlsx is the source of truth. Re-running the ingest script
  regenerates the fixture in place; reloading into a fresh DB is a
  one-shell-command reset.
- There are 29 cross-desk dependencies declared in the xlsx (mostly
  Publishing Tech and Surface Strategies). The mismatch flagger can lean
  on these at runtime without extra modelling.
