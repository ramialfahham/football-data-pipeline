# Review — fix/roster-exclude-non-entity-teams — 2026-07-06

> Blinded G3 review of the affiliation-mapping entity-integrity filter. Required reviewers for the
> staged paths: scope-auditor (always) + analytics-engineer-reviewer (dbt_project/**). Both PASS,
> no escalations.

diff_sha256: 7ef0bd5f3da10d85b49d0be80985cb2d35307e2b61e75dfd80baccd4eafa50c9

## scope-auditor
VERDICT: PASS
risks_checked:
- Both hunks are within `scope_paths` (the one 3_core model + `.claude/task/**`); no scope creep, no drive-by edits.
- Implements EXACTLY the CPO's option 1 (semi-join exclusion) — does NOT add All-Star teams to dim_team (option 2), does NOT weaken/delete the relationship test (option 3), does NOT touch squad ingestion; the CPO authority is recorded in the contract.
- impact_map honest: verified by grep that `mart_roster` is the only JOINing consumer (the other two mentions are doc-comments), and the 138-orphan / 118-All-Star-row drop is consistent with the semi-join.
- Semi-join grain preserved (DISTINCT extraction + filter-not-aggregate); the accepted trade-off (test becomes correct-by-construction) is disclosed in decisions_reserved.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Fanout: `dim_team.team_sk` is doubly deduplicated (base `qualify row_number() partition by team_api_id` + core `unique`/`not_null` test at core.yml) and the CTE adds `select distinct`, so the INNER JOIN is a provable semi-join — cannot duplicate rows or break the tested `(player_sk, team_sk, league_code, season_api_year)` grain.
- Silent over-filtering: `/teams` and squad `/players` are independently-scheduled loaders, so a transiently-missing real team could also be dropped by the same join — a genuine edge case, but explicitly disclosed + deferred (warn-count) in the contract's decisions_reserved, not hidden.
- Layer legality: dim_team is 3_core; layering.md forbids only core→stg_*/mart_* refs, and the model already refs a sibling core dim (dim_competition_season), so `ref('dim_team')` is a legal, consistent core→core pattern; no stg ref / json / union_all introduced.
- Type + downstream: `cast(pts.team_id as int64)` matches dim_team.team_sk's int64 cast (int64 already established in stg_apif__players); mart_roster inherits the fix via its unfiltered join and its own relationships→dim_team FK becomes correct-by-construction; CTE comma placement is valid.

## escalations
(none)
