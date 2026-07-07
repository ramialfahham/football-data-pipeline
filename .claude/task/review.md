# Review — docs/391-team-stats-benchmark-spec — 2026-07-07

> G3 Lock artifact. Team → Stats (vs-league benchmark) wireframe SPEC — new `docs/wireframes/14_team_stats.md`,
> field-bound to the built-but-orphaned `mart_team_competition_benchmarks` (rank-based "k of N" + vs-median +
> spread bar; no position dimension). Doc-only; the export wiring is GAP-23 (a later PR). Companion syncs:
> 00_overview (inventory + census), 99_gaps_register (GAP-23), 02_team_profile (▸Stats link). No board flip
> (the team-benchmark row goes green only when wired). Required set (routing): scope-auditor (always) + bi-analyst.
>
> Review journey (4 rounds): the bi-analyst caught four genuine LOCKED-contract defects in the draft, all fixed
> with judgment ([[feedback-decide-dont-escalate]]): (r1) `shot_accuracy` rendered despite being "defined but not
> displayed"; (r1) unbound `games` caption + clean_sheets "x/y" (mart carries only the rate); (r2) Shooting-funnel
> row order swapped; (r2) an ill-defined single-N header (team_count is per-metric); (r3) the Defending T·I·B trio
> rendered as separate rows despite being "sub-display of row 10 only". Round 4: both reviewers PASS on the
> corrected spec, whose rendered set now maps 1:1 to the LOCKED 16-row metrics_display team table (20 ranked, 16
> rendered; 10 higher_better + 5 neutral + 1 lower_better).

diff_sha256: 0d029ac1ee8716c58d929077a2212897b1c76b574d35724284f67595f6f34239

## scope-auditor
VERDICT: PASS
risks_checked:
- **Scope + no board flip.** All staged files within docs/wireframes/** + .claude/task/**; `content_architecture.md`
  is NOT in the diff — the team-benchmark row stays ⚠ orphan until wired (GAP-23), per the contract. Nothing
  code/model/seed/export smuggled.
- **§10 — no new decision.** The Defending fix (one ranked `defensive_actions_per_match` row + T·I·B sub-display)
  aligns to the LOCKED metrics_display 16-row table; the spec invents no metric/mechanism/product decision, and
  the rank-based display is what metrics_display already declares for the team benchmark. The separate-sub-screen
  placement was the CPO's approved plan call.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- **Defending-block LOCKED-contract compliance (the round-3 finding).** Re-verified against the wireframe + the
  actual `int_team_competition_benchmark_metrics_long` UNPIVOT: `defensive_actions_per_match` is now one ranked
  row with T·I·B as an explicit sub-display (not separate rows); tackles/interceptions/blocks appear only in the
  4-item mart-ranked-but-unrendered list, matching metrics_display's "defined but not displayed" list verbatim.
- **Rendered-set / count / direction-tally vs ground truth.** Counted the real UNPIVOT (20 metrics) and the real
  `metric_catalogue.csv` `direction` column for all 16 rendered ids: 20 ranked − 4 unrendered (shot_accuracy +
  T/I/B) = 16, block-by-block matching the LOCKED table; 10 higher_better + 5 neutral + 1 lower_better = 16 ties
  out exactly (`goals_against_per_match` the sole lower_better). Every rendered §5 row binds to a real column.
- **Naming variance (noted, non-blocking).** metrics_display spells `shots_on_target_per_match`; the real
  catalogue/mart/wireframe use `shots_on_goal_per_match` (the i18n key reconciles them). The wireframe uses the
  REAL column name; the variance is a pre-existing metrics_display transcription quirk, out of this doc's scope.

## escalations
- None open. No ESCALATE. All four bi-analyst findings across rounds 1–3 were display-correctness defects fixed
  with judgment (align to the LOCKED metrics_display contract + real mart columns); no CPO-class fork arose. The
  metrics_display `shots_on_target_per_match` vs `shots_on_goal_per_match` naming quirk is a separate, out-of-scope
  cleanup candidate (flag only).
