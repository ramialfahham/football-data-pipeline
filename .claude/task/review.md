# Review — feat/530b-player-penalty-openplay-catalogue — 2026-07-04

> G3 Lock artifact. #530(b): complete the two deferred PLAYER metric_catalogue rows (`goals_penalty`,
> `goals_open_play`) — fill base_relation=int_legs__player_match, numerator_expr (`sum(goals_penalty)`,
> `sum(goals_total - goals_penalty)`), direction=higher_better, + interpretation, mirroring the settled TEAM
> rows (#600) and the player `finishing_efficiency` row (#621). Plus a seeds/schema.yml note sync (drop the
> "still-deferred player rows" clause). No new metric, no model/export change; the player values already flow
> from int_player_season__metrics.
> Required set (routing for metric_catalogue.csv): scope-auditor + analytics-engineer-reviewer + football-analytics-expert-reviewer.
>
> **Round 1 (hash 4f458545):** football-analytics **PASS** + analytics-engineer **PASS** (flagged a non-blocking
> nit: my base_relation edit removed the word "deferred", leaving the numerator/denominator notes' "Blank for
> the deferred rows above" phrase dangling) + scope-auditor **ESCALATE** (is setting `direction` — a §10
> metric-meaning field — a new §10 decision needing a logged record, or an inherited classification?).
> **Resolution:** (a) reworded the two schema.yml notes to "Blank for the blank-base_relation rows above" (nit
> fixed); (b) recorded the direction classification in `.claude/task/escalations.log` (2026-07-04) as an
> INHERITED classification from the settled #600 team ruling + the #621 player-completion precedent,
> football-analytics-confirmed, CPO-approved via the ExitPlanMode plan approval this session — mirroring the
> #636 log-then-repass pattern (NOT a new CPO fork; a settled-ruling inheritance logged for trail completeness).
> The schema.yml reword changed the hash → all three reviewers re-run fresh.
> **Round 2 (hash e17eb665):** football-analytics **PASS** + analytics-engineer **PASS** + scope-auditor **PASS**.

diff_sha256: e17eb665cab709d0c4ba32aa2e3b25107564cac0501911241b7ad3e92d2672bc

## scope-auditor
VERDICT: PASS  (round 2; round 1 ESCALATE resolved by the escalations.log record)
risks_checked:
- **§10 audit-trail integrity (the prior ESCALATE).** Verified the direction=higher_better classification is
  now backed by a truthful logged record (`escalations.log` 2026-07-04): it is symmetric to the settled #600
  team ruling (team goals_penalty/goals_open_play both = higher_better in the seed), follows the #621 player
  precedent (finishing_efficiency/duels_won_pct player = higher_better), was football-analytics-confirmed, and
  the authority was surfaced in the plan's Design notes + CPO-approved via ExitPlanMode. Not a retroactive cover
  story, not an open fork — a settled-ruling inheritance. Prior ESCALATE resolved.
- **Scope + no drive-by.** Exactly the two intended catalogue rows changed; schema.yml note-only; task artifacts
  (contract, escalations.log) in `.claude/task/**`. All staged files within scope_paths; no model/export/site
  change; no new metric invented (metric_ids pre-existed; only blank fields filled; descriptions unchanged).

## analytics-engineer-reviewer
VERDICT: PASS  (round 2; round-1 dangling-note nit fixed)
risks_checked:
- **Resolvability against int_legs__player_match.** Read the model directly: `goals_penalty` exposed at
  int_legs__player_match.sql:96 (`coalesce(ev.goals_penalty,0)`) and `goals_total` at :74; both numerator_exprs
  (`sum(goals_penalty)`, `sum(goals_total - goals_penalty)`) resolve against real columns of the accepted
  base_relation, so `assert_metric_catalogue_expr_resolvable` (which now includes these rows, previously skipped
  as blank-base_relation) will pass. Formulas verified byte-equivalent to the live int_player_season__metrics
  computation (`goals - goals_penalty as goals_open_play`) — not invented values.
- **CSV integrity + schema.yml consistency.** 14/14 columns on both changed rows; row 31 correctly double-quoted
  (internal commas), row 32 unquoted (no commas); denominator_expr/importance_tier/group_display_order blank,
  matching the team-row shape. schema.yml `base_relation` no longer says "still-deferred", and the
  numerator/denominator notes were reworded to "blank-base_relation rows above" (no dangling self-reference).
  Drift guard `assert_no_uncatalogued_season_metric` unaffected (rows already catalogued; it checks metric_id
  presence, not expr fill). Non-blocking residual noted (out of scope, spawned as a follow-up): a stale
  "deferred" comment survives in the sibling `assert_metric_catalogue_expr_resolvable.sql:7-8`.

## football-analytics-expert-reviewer
VERDICT: PASS  (round 2; unchanged CSV formulas re-confirmed)
risks_checked:
- **Formula asymmetry vs the team row (own-goal term).** Traced `goals_total` end-to-end (stg → fct →
  int_legs__player_match, zero own-goal adjustment) and corroborated by the independent
  int_player_season_position__metrics.sql:38 comment + a memory reconciliation: player `goals_total` already
  excludes own goals, so player open-play = `goals_total - goals_penalty` (two terms, NO `- goals_own`) is
  football-correct, distinct from the team row's three-term `goals_for - goals_penalty - goals_own` (team
  goals_for is the scoreline, which credits own goals). `sum(goals_penalty)` is the right penalty definition.
- **Direction + purity + interpretation.** direction=higher_better is football-sound (goals for the player/team;
  benchmarked within position-group so more is better even for defenders — distinct from contribution_share's
  NEUTRAL cross-position share). numerator_expr is a pure aggregate (no coalesce/countif/null-gate in the
  catalogue expr; the base leg's coverage handling is pre-existing, correctly the model's job). The open-play
  interpretation correctly says "excl. penalties" only (no "and own goals"), matching the formula.

## escalations
- (§10 direction classification) RESOLVED — recorded in escalations.log 2026-07-04 as a settled-ruling
  inheritance (#600 + #621), CPO-approved via ExitPlanMode. No open escalation.
