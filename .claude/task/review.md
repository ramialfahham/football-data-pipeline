# Review — feat/a1-deserved-vs-actual-team-profile — 2026-06-29

> Blinded review cycle (G3). Required set for the staged paths (dbt_project/models/**):
> scope-auditor (always) + analytics-engineer (dbt_project/**). NOT football-analytics —
> metric_catalogue.csv is untouched (deserved_rank/sot_rank_gap already catalogued, #598).

diff_sha256: 8681b707cbfe42bcecf8e6485923055ea995bf1464ab018c6f0103b107e412bb

## scope-auditor
VERDICT: PASS
risks_checked:
- Join grain and cardinality: int_team_season__deserved_vs_actual is grain (team_sk, season_sk); the left join matches both keys; the intermediate produces one row per input (single rank() over subset partition keys, no aggregation fan-out), so the mart's existing unique_combination_of_columns(team_sk, season_sk) cannot be violated.
- NULL semantics + §10/scope: deserved_rank and sot_rank_gap NULL together for non-rankable league-seasons (the coverage gate requires every team to have both sot_difference and standing_rank); no §10 decision taken unilaterally (placement = CPO Option 1; metrics pre-catalogued #598); scope is exactly the 3 declared files; impact_map present and evidenced (leaf mart). Non-blocking note: the intermediate's domestic_league/ folder is organizational, not a compile-time filter — pre-existing, sound, out of scope here.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Grain fan-out: int_team_season__deserved_vs_actual carries a tested unique on team_season_sk (surrogate over team_sk, season_sk); the join keys match the intermediate's grain exactly; one row in → one row out (rank() partitions on subset keys). No row multiplication; mart grain test is the backstop.
- latest_rank == actual_rank identity: both are standing_rank from the SAME int_team_season__standings_primary model on (team_sk, season_sk) (tested unique grain), so sot_rank_gap reconciles exactly with the displayed latest_rank — confirming the decision to surface no redundant actual_rank. Also verified: NULL propagation safe (existing IS NULL OR ... tests untripped), consumption layer does no computation (_strip_identity denylist excludes the new cols → they pass through verbatim), layer direction correct (mart→intermediate), additive columns on a table mart (no incremental hazard).

## escalations
(none)
