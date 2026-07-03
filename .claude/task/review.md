# Review — feat/player-contribution-share — 2026-07-03

> G3 Lock artifact. Phase D "bonus" flagship read — player contribution-share: a NEW
> `int_player_profile__contribution` (goal-involvement share of the club's WHOLE-SEASON goals) +
> composition into `mart_player_profile` + a `metric_catalogue` row for `contribution_share`.
> Required set (routing): scope-auditor (always) + analytics-engineer-reviewer (`dbt_project/**`) +
> football-analytics-expert-reviewer (`dbt_project/seeds/metric_catalogue.csv`).
>
> Round 1 (hash 465f31e9) — scope-auditor PASS; analytics-engineer **FAIL (A1)**: `contribution_share`
> + its atoms shipped to the export with NO `metric_catalogue` row, and `goal_involvements` duplicated
> the already-catalogued `scorer_points`. Fix: catalogued `contribution_share` as a flagship-output row
> (BLANK base_relation — the `deserved_rank`/`sot_rank_gap` pattern; direction=neutral, CPO
> AskUserQuestion 2026-07-03) + renamed the numerator atom `goal_involvements` -> the existing
> `scorer_points` + amended the contract (added `metric_catalogue.csv` to scope; the widening pulled in
> the football-analytics reviewer). Round 2 (hash ccca23dd) — **analytics-engineer PASS** (A1 resolved),
> **football-analytics PASS**, **scope-auditor PASS**. All three required reviewers PASS on the SAME hash.

diff_sha256: ccca23dd86b9bc235310530b7c695481179967151ebe2f60c5aa1b2e71e47685

## scope-auditor
VERDICT: PASS  (round 2; round 1 also PASS)
risks_checked:
- **Scope widening authorized + logged.** The amendment adds `metric_catalogue.csv` to `scope_paths` with
  the authority stated (the AE A1 finding, which is governance-required + the CPO direction ruling); all
  five changed paths fall within the amended scope. The three metric-definition rulings (numerator,
  denominator, direction=neutral) are each a CPO AskUserQuestion 2026-07-03 recorded in `escalations.log`
  — no silent §10. The scope expansion (catalogue + the football-analytics reviewer) was CPO-confirmed.
- **Catalogue-fix honesty + impact_map fidelity.** `contribution_share` is catalogued as a flagship-output
  row (blank base_relation, the `deserved_rank`/`sot_rank_gap` precedent — the resolvability guard skips it);
  `goal_involvements` is reconciled to the catalogued `scorer_points` (not a new duplicate name);
  `team_goals_season` is the carried denominator component (the benchmark carried-atom precedent). The
  impact_map is evidenced (writers/downstream/layer_rules/deploy_order/blast_radius). No export / wireframe /
  layering / schema-drift churn. Grain (player_sk, team_sk, season_sk) unique; denominator-zero -> NULL via
  safe_divide; the 0..1 invariant test present.

## analytics-engineer-reviewer
VERDICT: PASS  (round 2; the round-1 A1 FAIL is resolved)
risks_checked:
- **A1 resolution, mechanically verified.** Read `assert_metric_catalogue_expr_resolvable.sql` directly and
  confirmed the `{% if base in base_cols %}` gate genuinely SKIPS blank-`base_relation` rows —
  `contribution_share` is skipped exactly like `deserved_rank`/`sot_rank_gap`, NOT trusting the contract's
  prose. The other three catalogue-integrity tests each independently exempt/ignore the new row for a
  distinct verified reason: `assert_team_metric_meaning_complete` (entity in team/team+player — player is
  exempt), `assert_metric_catalogue_unique_by_entity` (fresh (metric_id, entity) key, no collision),
  `assert_no_uncatalogued_season_metric` (hardcoded to the three season rollups, none of which is this
  model). `team_goals_season` remaining uncatalogued is accepted as the ratio's display-denominator
  component (the benchmark carried-atom precedent — a defensible read, not a rubber stamp).
- **Rename correctness + no column collision.** Zero `goal_involvements` residue in code (repo-wide grep;
  the string survives only in doc/patch prose). The pre-existing `int_player_season__metrics.scorer_points`
  is NEVER selected into `mart_player_profile` (no `a.scorer_points`, no `a.*`) — so the new `c.scorer_points`
  off the contribution CTE is the sole occurrence reaching the mart's output schema; no ambiguous / shadowed
  column via `select *`. Model logic (grain, the `(fixture_sk, team_sk)` numerator join, the
  `(team_sk, season_sk)` denominator join, safe_divide, the 0..1 invariant) is byte-identical to round 1
  except the label swap; the mart join is additive/nullable (left join, mirrors the YoY join above it);
  layer placement complies with layering.md §4_intermediate (composes two int legs, no mart/staging ref).

## football-analytics-expert-reviewer
VERDICT: PASS  (round 1 — added to the required set by the scope widening)
risks_checked:
- **Formula soundness + the 0..1 invariant.** "Goal involvements (goals + assists) / the club's whole-season
  goals" is a standard, meaningful "involved in X% of the team's goals" framing; the numerator reuses the
  catalogued `scorer_points` (closing the A1, not duplicating it). The 0..1 range is a STRUCTURAL guarantee of
  the `(fixture_sk, team_sk)` inner join (a player's counted goal only comes from a fixture whose team
  `goals_for` already includes it), not an artificial cap. The whole-season denominator is a defensible CPO
  product choice, coherent with the "share of the club's goals" read.
- **Metadata + the formula-vs-availability rule.** direction=neutral is football-correct (involvement-share is
  position-dependent — strikers high, defenders low by role, not by quality; consistent with the catalogue's
  neutral style metrics); format=percent, metric_group=goals, lower_is_better=false all correct. The honest
  limit (the share understates where the player's per-match stats are missing — whole-season denominator vs
  covered-appearance numerator) lives in the description/model prose ONLY — there is NO coalesce / countif /
  coverage-gate baked into the (blank) exprs, respecting the formula-vs-availability rule. No fabricated
  good/bad colour, no over-claimed cap. The mismatch is a CPO-accepted documented limit (escalations.log
  2026-07-03), not a defect this diff introduces.

## escalations
- (metric definition — AskUserQuestion 2026-07-03, RULED) contribution-share's numerator / denominator /
  direction were put to the CPO before building: numerator = goal involvements (goals + assists); denominator
  = the club's WHOLE-SEASON goals_for (CPO accepted the understatement-where-stats-missing honest limit);
  direction = NEUTRAL. Durable record: `escalations.log` 2026-07-03.
- (scope — AskUserQuestion 2026-07-03, RULED) The analytics-engineer A1 FAIL required cataloguing
  `contribution_share`; the CPO confirmed widening scope to `metric_catalogue.csv` + adding the
  football-analytics reviewer (via the same direction ruling). Fixed: catalogued `contribution_share` +
  reconciled `goal_involvements` -> `scorer_points` + amended the contract. No open escalations.
