# Review — feat/player-profile-yoy — 2026-07-03

> G3 Lock artifact. Phase C brick 1 — player year-over-year: a NEW `int_player_profile__yoy` (the player
> mirror of the shipped team YoY `int_team_profile__yoy`) + its yml + composition into `mart_player_profile`.
> dbt-only. Required set (routing): **scope-auditor (always) + analytics-engineer-reviewer (`dbt_project/**`)**.
> No export/wireframe/ingestion/CI path touched → no cto / bi-analyst / data-engineer.
>
> Round 1 (hash 0618425a) — scope-auditor PASS; analytics-engineer FAIL (one finding: the YoY columns were
> named `shots_on_target_*`, inconsistent with the metric-catalogue id `shots_on_goal` + the sibling
> `a.shots_on_goal` already in the mart — two names for one stat). Fix: renamed the YoY columns
> `shots_on_target_* → shots_on_goal_*` (name-only, both .sql files). Round 2 (hash f6407a8a) — BOTH PASS on
> the same hash. The metric-set CPO ruling is durably logged (escalations.log 2026-07-03).
>
> **Rebound onto a070646** (2026-07-03) after sibling PR #637 merged first — only the `.claude/task/*` scratch
> files conflicted; the 3 dbt models + contract.md are BYTE-IDENTICAL to the r2 review (they were not in the
> rebase conflict set; contract.md resolved to the Phase-C version). Only contract.md's diff BASE shifted
> (#636's doc-sync → #637's handover contract), so the hash re-anchored f6407a8a → 1e4ea2db; the r2 PASS
> verdicts carry unchanged (same content).

diff_sha256: 1e4ea2db8ff4b35a1d445507a2216f38dfbb7442cb89b50419d82466456f916f

## scope-auditor
VERDICT: PASS  (round 2; round 1 also PASS)
risks_checked:
- Multi-club grain alignment + join safety: the mart↔YoY join on (player_sk, team_sk, league_code,
  season_api_year) is 1:1 at the output grain (the `cur` CTE qualifies to one row per player-club-league;
  the LEFT JOIN yields NULL for prior-season-absent / older seasons); the rare same-league two-club-in-one-season
  case surfaces the primary club's YoY only (via int_player_season__team, documented honest limit). Grain is
  tested by unique_combination_of_columns.
- Contract↔code naming + no silent metric change: the rename `shots_on_target → shots_on_goal` aligns the
  column to the metric-catalogue id (metric_catalogue.csv row 34) + the sibling `a.shots_on_goal` (mart line
  120) — a catalogue-driven ENGINEERING consistency fix, NOT a product decision. The contract's "shots on
  target" is the CPO's product term (escalations.log 2026-07-03, "broader per-position set"); the column uses
  the catalogue engineering name — a faithful concept→column mapping. Blast radius = the NEW additive YoY
  columns only (existing mart numbers unchanged; export auto-carries via select *, #606 precedent); scope is
  exactly the new int .sql/.yml + mart_player_profile + .claude/task/**. No §10 made without authority.

## analytics-engineer-reviewer
VERDICT: PASS  (round 2; round-1 FAIL finding resolved)
risks_checked:
- Rename completeness + no collision: grep confirms zero residual `shots_on_target` column identifiers; every
  YoY column (int_player_profile__yoy cur/prev/final + mart select/join) now reads `shots_on_goal_*`,
  matching the catalogued player metric_id and the sibling `a.shots_on_goal`. The base season total
  `a.shots_on_goal` (line 120) and the YoY derivatives `y.shots_on_goal_this_season/_prev_season/_delta_yoy`
  are four distinct, non-colliding output columns (verified against the full select list).
- No regression from the name-only fix: cur/prev alignment (appearance-cutoff N; prior season through its
  first N via `match_number <= cutoff` + qualify), the delta math (cur − prev), the grain +
  unique_combination test, the 4-key mart left-join composition, the relationships to dim_player/dim_team
  (transitively guaranteed by the fct-level tests, core.yml), and the drift-guard exemption
  (assert_no_uncatalogued_season_metric scans only the 3 season-rollup models, not this profile model) all
  hold unchanged from round 1. Layer contract: intermediate refs an int + a seed only (no mart ref);
  mart_player_profile is the sole consumer.

## escalations
- (product, AskUserQuestion 2026-07-03 — RULED) The YoY metric set (which stats get the "this season vs last"
  delta) is a product choice; three options presented with a recommendation. CPO ANSWER: **the broader
  per-position set** — goals, assists, shots-on-target (catalogue column `shots_on_goal`), key passes,
  defensive actions (tackles + interceptions + blocks). Durable record: escalations.log 2026-07-03. The
  grain/composition (per-club, primary-club attach) is an engineering call decided in the contract, not
  escalated. No open escalations remain.
