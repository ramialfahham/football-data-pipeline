# Review — feat/mart-player-career — 2026-06-23

diff_sha256: 98da1b18c08c99ffa9a027c94de9c81dde2a3156120390f07ee918ae52a68e85

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Cross-model column existence + grain: verified every column int_player_career__metrics reads from
  int_player_season__metrics (player_sk, league_code, league_sk, season_sk, season_api_year,
  appearances, goals, assists) and every column mart_player_career reads from the rollup / dim_player /
  the seeds exists. The GROUP BY (player_sk, league_code) matches the surrogate-key grain exactly;
  any_value(league_sk) is safe (0 league_codes map to >1 league_sk, BQ-verified); unique_combination
  test guards it. No fan-out.
- Catalogue governance: NO new/uncatalogued metric — `appearances` is an exempt playing-time fact (drift
  test exempt list); `goals`/`assists` are catalogued player metrics and the catalogue is window-agnostic,
  so career totals are the same atoms over a career window. `national_appearances_total` is a denormalised
  fact computed in dbt (window sum), not in the export — consumption-layer rule honoured. mart_player_career
  is correctly added to layering.md's "exhaustive" mart inventory. (Non-blocking: a not_null guard on
  entity_type would harden against an unmapped competition; bounded — all active comps are registered.)

## scope-auditor
VERDICT: PASS
risks_checked:
- Rollup grain safety: int_player_career__metrics aggregates int_player_season__metrics (one row per
  player-season) by (player_sk, league_code), summing appearances/goals/assists across seasons — no hidden
  duplication; the unique_combination test enforces one row per grain.
- Denormalisation without double-count: national_appearances_total is a window sum over (partition by
  player_sk); the intermediate's grain uniqueness prevents double-counting. Scope is honest — additive
  only (no existing model/number changed); the impact_map pastes source-depth evidence; the layering.md
  addition is a recorded clean-tree amendment (authority: the reviewer FAIL + the exhaustive-inventory rule);
  the national figure is honestly labelled "national appearances in covered competitions", not caps.

## escalations
(none)
