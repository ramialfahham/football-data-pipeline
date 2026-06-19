# Review — feat/mart-roster — 2026-06-19

> PR 1 of split task A: add `mart_roster`, the identity-only club squad list (mart-only; no
> export wiring — Squad-block consumer is in PAUSED #391). Round 3 of the cycle: round-1
> analytics-engineer FAIL (silent-drop guard + undocumented first/last name) fixed via a
> contract amendment (+ core.yml relationships test) and dropping the columns; round-2 FAIL
> (undocumented `league_sk`) fixed by dropping it. Both reviewers now PASS on the current
> staged diff. Required reviewers for the staged paths (dbt_project/** + always): scope-auditor
> + analytics-engineer-reviewer.

diff_sha256: 0a4c9f2173fae2c61983c0039a0b04a3577448c5125d2ed1f65e7c588a42913d

## scope-auditor
VERDICT: PASS
risks_checked:
- Spec-compliance of the league_sk removal: the contract's grain (team_sk, league_code, season_api_year, player_sk) and identity column list (name, listed position, nationality, birth_date, photo) do not include league_sk; removing this undocumented column, redundant with the league_code partition key, aligns with the locked spec and breaks nothing in a not-yet-shipped model.
- Scope-boundary integrity: every edit is confined to the amended scope_paths (mart_roster.sql, shared.yml, core.yml, layering.md, contract.md); no protected path, no export/consumption logic, no leakage from the companion mart_leaderboards PR. The core.yml relationships guard is authorized under the fix-don't-escalate rule + DQ-non-negotiable standing rule and was verified clean against live data (0 unregistered league_codes).
- Contract amendment legitimacy: the clean-tree amendment records the analytics-engineer FAIL as authority for adding core.yml to scope; proportionate to the finding (a one-line guard), not scope creep.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Column-set exact-match audit: the SELECT emits 13 columns (player_team_season_sk, team_sk, player_sk, season_sk, league_code, season_api_year, competition_type, entity_type, player_name, player_position, player_nationality, player_birth_date, player_photo_url) and the shared.yml mart_roster block documents exactly those same 13 — no SELECT column missing from the yml, no documented column absent from the SELECT. league_sk absent (round-2 finding resolved); player_first_name / player_last_name absent from both (round-1 finding resolved).
- Fan-out risk on the LEFT JOIN chain: the registry join is on league_code (unique in competition_registry) and the types join on competition_type (unique in competition_types) — neither can multiply mapping rows; player_team_season_sk stays unique. The post-WHERE silent-drop of an unregistered league_code is covered by the new relationships test dim_player_team_season_mapping.league_code -> competition_registry.league_code (core.yml), confirmed intact.
- Grain / null handling / layer: grain (team_sk, league_code, season_api_year, player_sk) holds; season_sk correctly nullable + untested; no computation in the SELECT (consumption contract satisfied); view materialization consistent with the identity projection.

## escalations
(none)
