# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-04 (end of session — #327 PR #336 open; next: CI green → merge → start #320)_

## Current focus
Building the **metrics context-model foundation** (epic **#317**) — the shared
context/window model + metric layer that all team/player performance marts consume.
Full design: `docs/metrics_context_model.md` (on main). Reasoning/history: memory
`project_metrics_context_model.md`.

## Status
- ✅ **#318** merged — `competition_types` seed (club/national) + CI coverage check.
- ✅ **#319** merged — `competition_registry.csv` seed (league_code→competition_type) +
  three shared building-block legs in `dbt_project/models/4_intermediate/shared/`:
  `int_legs__team_match`, `int_legs__player_match`, `int_legs__team_from_players`.
- ✅ **#331** merged — enforced cross-chat handover: global hooks + this file.
- ❌ **PR #333 closed (wrong)** — wrong metric IDs (window suffixes), missed team_from_players metrics.
- ✅ **Issues #327 + #320 re-specced** — read their issue bodies before starting any build.
- 🔁 **PR #336 open** — `feat/327-metric-catalogue`. Adds `metric_catalogue.csv` (38 rows:
  19 team + 19 player), window-agnostic IDs, schema.yml entry. **Merge before starting #320.**

## Next concrete action (build order)

### 1. Merge [PR #336](https://github.com/ramialfahham/football-data-pipeline/pull/336) (#327)
Wait for CI green then merge. The catalogue is done.

Key rules (do NOT deviate):
- **Window-agnostic metric IDs** — no `_recent`, `_pretournament`, or any window suffix.
  The ID is the metric name only. Window is context applied at query time (#320).
- **Three source pools** — all must be covered:
  - `int_legs__team_match` → 13 team metrics:
    `league_rank`, `points_won`, `goals_per_match`, `goals_against_per_match`,
    `shots_per_match`, `shot_accuracy`, `danger_zone_ratio`, `finishing_efficiency`,
    `passes_per_match`, `pass_accuracy`, `corner_kicks_per_match`,
    `corners_conceded_per_match`, `save_ratio`
  - `int_legs__team_from_players` → 6 new team metrics (player stats aggregated to team level):
    `key_passes_per_match`, `tackles_per_match`, `interceptions_per_match`,
    `blocks_per_match`, `duels_won_pct`, `dribbles_success_pct`
  - `int_legs__player_match` → 19 player metrics:
    `goals`, `assists`, `shots_on_target`, `dribbles_success`, `dribbles_attempts`,
    `dribbles_success_pct`, `passes_key`, `passes_accurate`, `passes_total`,
    `pass_accuracy_pct`, `duels_won`, `duels_total`, `duels_won_pct`,
    `tackles_total`, `tackles_interceptions`, `tackles_blocks`,
    `save_pct`, `cards_yellow`, `cards_red`
- **Totals in int_, calculations in marts** — `int_legs__team_from_players` carries
  raw sums (duels_won, duels_total, etc.); the catalogue documents the mart-level
  formulas (ratios, per-match rates) that use those totals.
- **No CI check** in this issue (deferred to #321 when manifest gets window-agnostic names).
- **No schema-YAML backfill** on existing marts (retired in #321).

### 2. #320 — momentum builder + marts
Read updated issue #320 body. Key design decisions locked:
- **Season boundary = `season_api_year` from fixture data** (data-backed, no manual
  maintenance, no date inference). Cross-competition last-5: filter legs to
  `season_api_year = upcoming_fixture.season_api_year` across same entity_type.
  Previous season fallback: `season_api_year - 1`.
- **Full window matrix** per competition_type × phase in the issue body.
- **Player windows** mirror team windows using `int_legs__player_match`.

### 3. #321 — de-hardcoding cut-over
Retire `int_matchday__*`/`int_wc__*`, the `mart_matchday_insights`/`_wc`/`_bl1_relegation`
variants, BL1/BL2/L1 round vars. Parallel-run + validate. CI check (manifest → catalogue)
lands here when manifest is updated to window-agnostic names.

## Do NOT
- Do **not** put window suffixes in metric IDs (`_recent`, `_pretournament`, etc.).
- Do **not** add descriptions/tests to `mart_matchday_insights`, `_wc`, or
  `mart_matchday_player_insights` — they are retired in #321.
- Do **not** use dbt MetricFlow / Semantic Layer — use the catalogue **seed**.
- Do **not** infer season boundaries from dates or status flags — use `season_api_year`.
- Do **not** start coding before restating the spec and getting approval.
- **Read `project_metrics_context_model.md` memory AND the updated issue body before
  any build.** Previous chats drifted by skipping one or both.

## Conventions reminder
- Bash for all commands; branch from main before writing any file.
- `validate-local` + `sqlfluff lint models/...` before pushing.
- Issue **body** is the contract — if it's not fully specified there, stop and ask.
