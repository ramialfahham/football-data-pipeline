# Review — docs/player-performance-surface-spec — 2026-06-17

> Player performance-surface spec (docs only): new §8 in docs/metrics_context_model.md resolving
> the §7 player deferral, + a supersession note in docs/player_metrics_catalogue.md. Reviewers:
> scope-auditor (routing-required for these docs paths) + analytics-engineer-reviewer +
> football-analytics-expert-reviewer (CPO-directed for the analytics-design + football-domain
> content). Two analytics-engineer FAIL rounds were fixed (surrogate key stated; NT-context
> selector forced to the intermediate layer with its anchor; last-appearance/minutes declared as
> mart columns; form_window_kind set shown derivable + reserved to build) and re-reviewed clean.
> football-analytics reviewed the national-context reframe, the override rationale, and the
> weighted-ratio rule — all byte-unchanged by the subsequent fixes (which touched only grain
> representation, layer placement, mart columns, and enum hygiene), so its PASS carries.

diff_sha256: 9d06360b9e2fa4aa87fffd714746136d8e50333c500c50c61532a6065c7f8030

## scope-auditor
VERDICT: PASS
risks_checked:
- NT-context selector (a third selection shape) is reserved to #484 — the spec prescribes the *what*
  (cross-comp within national, no season cap, ≤5 by recency, national-team-anchored) but defers the
  model name and grain; no unilateral new mechanism (A3) is introduced in this docs change.
- The national-window override is a §10 rule reinterpretation — and it is recorded, not silently
  taken: a dated CPO override in decisions_taken, the catalogue's Form-window dispatch marked
  SUPERSEDED with a pointer to §8, football-analytics validation routed with an escalation fallback.
- Scope: every hunk is within scope_paths (the two docs); the locked metrics_display.md and the
  metric_catalogue seed are untouched; the appearance/playing-time display amendment is explicitly
  reserved to a bi-analyst-owned follow-up, not made here.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Consumption-layer (A5): avg-minutes-per-appearance and the last-appearance pick are declared as
  mart columns (`max(kickoff)` + opponent join in the model; export formats only) — no derivation,
  ranking, or "latest" selection leaks into the export/UI.
- Surrogate-key collision under per-club grain: the spec identifies that the existing
  `(player_sk, season_sk)` key is non-unique when a player transfers mid-season, mandates the
  full-grain key `(player_sk, team_sk, league_code, season_sk)` + a `unique` test, with the key
  name reserved to #480 (a build-time naming call).
- Layer + aggregation soundness: "one aggregation, two windows" over the per-match leg is consistent
  with the existing momentum / season-record builders and the selection-vs-aggregation rule; the
  weighted-ratio rule matches the catalogue (clarifies, does not redefine); the form_window_kind set
  is shown derivable from the matrix with labels reserved to build.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Sparse national-team data (late call-ups / injury returns): the honest-absence rule + the
  last-appearance meta-line surface `0 of N · —` truthfully, rather than substituting a domestic-club
  proxy that answers a different question — the override is football-sound under the context framing.
- Friendly-match opposition quality in the NT pool (once ingested): handled by the context-not-form
  reframe, the no-opponent-exclusion principle, and opponent-context rows; the weighted-ratio
  aggregation (`sum num / sum den`, never an average of per-match %s) is confirmed football-correct.

## escalations
(none)
