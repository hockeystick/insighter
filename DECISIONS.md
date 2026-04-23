# Decisions — status after Thursday resume

## Resolved

- **#1 Level scale**: split. `level` enum is now Unknown / Aware / Practising /
  Embedded (depth only); `led_by_champion: bool` is a separate field for
  bus-factor-at-capability. Migration `capabilities.0003` applied. Commit
  `942a337`.
- **#2 License**: MIT. `LICENSE` file committed (`6bb941f`).

## NEW BLOCKER — #7 Taxonomy granularity: L2 vs L3

The xlsx has three hierarchy levels: **L1 cluster → L2 subcluster → L3 task**.
Metadata (Priority, Baseline, Template-able, Phase, Assessment, Secondary)
lives on **L3 tasks**, not on L2 subclusters.

Our current `CapabilityItem` maps to **L2 subcluster** (e.g. "Service
blueprint", "Loyalty ladder"). The xlsx has 90 distinct L3 tasks across 54
L2 subclusters in 12 L1 clusters. A single L2 typically has 1–4 tasks.

**The shape mismatch, concretely:**
- Current fixture: 9 clusters × 43 items (L2, no metadata)
- xlsx truth: 12 clusters × 54 L2 subclusters × 90 L3 tasks (metadata per task)
- Within L2 groups that have >1 task (25 such groups), metadata **varies**
  for most fields: Priority varies in 17/25 groups, Baseline 13/25,
  Template-able 15/25, Phase 13/25. Assessment is mostly stable (7/25 vary),
  Secondary mostly stable (9/25).

So: there's no lossless way to push task-level metadata onto L2 items
without either schema change or aggregation that discards signal.

**Also**: the xlsx has clusters the brief omitted — `Video Audience`,
`Community & Engagement Infrastructure`, `Assessment & Baseline`, and
`Analytics & First-Party Data` (vs our `Analytics & first-party data`, case
difference). Cluster wording and ordering differs too.

### Options

- **(a) L3 = CapabilityItem.** Rebuild the fixture from the xlsx. Items
  become tasks (90 instead of 43). Clusters updated to match xlsx (12 not
  9). Schema unchanged. Most honest mapping to the source of truth; best
  for the demo because each item carries real metadata. Biggest fixture
  rewrite.
- **(b) L2 stays, aggregate metadata.** Keep current 43 items. Collapse
  task-level metadata to L2 (majority vote, or highest priority across
  tasks). Lossy; ~70% of L2 groups have varying signal that gets
  flattened. Smallest change, but defensibly wrong.
- **(c) L2 keeps structural role, add L3 model.** Add a `CapabilityTask`
  model as a child of `CapabilityItem`, carrying the metadata. Most
  expressive. State history still lives at L2 (one row per subcluster per
  outlet). Biggest schema change; may or may not be worth it for v0.1.
- **(d) L2 items, metadata only where task-level is consistent.**
  Populate only the fields that are uniform across an L2 group. Mixed
  signal; messy.

### Recommendation

**(a).** The plan's "source of truth is the diagnostic" stance means the
capability structure should match what the desk actually uses. The
30/60/90 behavioural check-in and practice-adoption framing reads better
at task granularity anyway ("are they running personas?" not "are they
doing audience research?"). And it's the cleanest thing to demo.

Cost: one fixture rewrite and an update to the `outlet_detail` template's
grid rendering (group by L1 cluster, show task name under it). No model
changes. Existing `CapabilityState` rows would need re-keying, but there
are no seed state rows yet, so no data loss.

**Default if no answer**: (a) on next resume.

## Still pending

- **#4 Mismatch flagger prompt**: Friday scope.
- **#5 Seed outlet voices + diagnostic notes**: yours to write.
- **#6 Demo UX polish**: Saturday.
