# Review — feat/391-gap16-player-team-affiliation — 2026-06-30

> G3 Lock artifact. #391 GAP-16 — player team affiliation (current team + per-season history). dbt build
> (new int_player_season__team + mart columns + relationships DQ test) + export reshape + folded wireframe/
> register doc-sync. Required set (routing): scope-auditor (always) + analytics-engineer (dbt_project/**) +
> cto (scripts/export_*.py + tests/**) + bi-analyst (docs/wireframes/**). All four fresh at this hash.

diff_sha256: 752bc98494eca1f421b1dc4861abff5b018d595b6e15825e9c5923b57eea6ae1

## scope-auditor
VERDICT: PASS
risks_checked:
- Grain-alignment + LEFT JOIN safety: int_player_season__team grain (player_sk, league_code, season_api_year) is 1:1 with the mart's (player_sk, season_sk) (season_sk = sk(league_api_id, season)); the unique_combination test enforces it; coalesce(is_current_team, false) handles honest absence. No fan-out/drop.
- Consumption-layer: shape_player_payload selects current_team by the dbt is_current_team flag (no independent re-rank); the test deliberately flags 2024 (not the latest 2025) so it would fail if the export re-ranked; internal keys (team_sk, is_current_team) stripped from published season rows. dbt owns the ranking.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Fan-out on the mart LEFT JOIN to int_player_season__team: join keys (player_sk, league_code, season_api_year) are the exact (tested-unique) grain of the new int; the mart spine int_player_season__metrics shares that grain → provably 1:1, no fan-out.
- Duplicate team_sk: int_player_season__metrics already exposes team_sk on alias `a`, but the mart SELECT is fully explicit (no a.*) and emits only ta.team_sk — no duplicate column/ambiguity in the output.
- Consumption-layer + materialization + drift guard: export reads the flag, never re-ranks; _strip_identity drops team_name/logo/country, the pop removes team_sk/is_current_team; both new int + mart are table-materialized (no incremental rename / no --full-refresh); the drift guard (assert_no_uncatalogued_season_metric) targets only the two *__metrics ints — the new int's non-metric columns are not inspected.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Flag-read vs re-rank: shape_player_payload gates current_team on r.get("is_current_team") with no sort-and-pick; the test flags the 2024 row while 2025 exists, so current_team=Bayern(157) — it would fail (=Real Madrid 541) if the export used "latest season". Valid falsifying case.
- Identity-key leak + regression: _strip_identity drops team_name/logo/country before they can appear as flat keys; the pop loop removes team_sk/is_current_team (safe on absent keys); null team_sk → None honest absence (no raise); the pre-existing player test (rows without team cols) still passes because all new paths fail-safe to None. Export wired into no workflow (live MVP isolated); no new import/cost.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Field-binding/key-name consistency across mart → export → wireframe: §3 enumerates current_team + seasons[].team; the export emits {team_id,name,crest,country} (team_id from team_sk, identical to _fixture_side); §5 binds the same keys + source int_player_season__team. No spelling drift.
- Locked display contract: metrics_display.md not in the diff; the 9 locked player bundles unchanged; team affiliation is identity (no %/rate/KPI); the §8 SEO memberOf + §4 ASCII edits are spec-accuracy, not a new rendered-metric label/treatment. §5 source corrected ("latest match-log row" export-side → dbt-derived most-recent-match); register GAP-16 marked shipped + Option-B (cf. GAP-14/GAP-18 format); §10 GAP-16 line removed; GAP-08/GAP-12 intact; no stray open "GAP-16".

## escalations
(none) — all four required reviewers PASS at this hash; no FAIL, no ESCALATE. The Option-B source ruling, the naming, and the doc-sync fold were CPO-directed this session (presented decisions + plan approval), recorded as such (not silently self-granted).
