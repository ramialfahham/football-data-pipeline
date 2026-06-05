# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-05 (audit + validation session — #337 merged; #321 scope refined; next: build mart_fixture_preview then delete old models)_

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
- ✅ **#327 merged** (PR #336) — `metric_catalogue.csv` (42 rows: 19 team + 23 player),
  window-agnostic IDs, schema.yml entry.
- ✅ **#320 merged** (PR #337) — `int_momentum__team`, `int_momentum__player`,
  `mart_momentum__team`, `mart_momentum__player` in `shared/`. Validated: VL numbers
  match old mart exactly. WC comparison deferred to #326 (old mart was cumulative W2,
  not comparable to W1).

## Key design decisions locked in #320 (do NOT re-debate)
- **W1 scope:** all competition types, club and national. Shown alongside W2 for every fixture.
- **Club season boundary:** `season_api_year` cap — real calendar boundary.
- **National season boundary:** no cap — qualifying campaigns span multiple API seasons;
  recency alone is the correct boundary.
- **W1 vs W2 split:** W1 = last 5 (this PR). W2 = cumulative season-to-date (#326, deferred).
  W2 for national: qualifying during = cumulative campaign; WC/EURO = tournament cumulative.
- **No club/national split at intermediate layer** for W1 — difference is one conditional
  in the JOIN. Split makes sense at W2 where logic truly diverges.
- **docs/metrics_context_model.md §4:** `qualifying during` corrected to
  "All matches so far in this qualifying campaign" (was incorrectly "Last 5").

## Next concrete action (build order)

### #321 — de-hardcoding cut-over (refined scope — read before branching)

**Two-step execution:**

1. **Refactor `mart_matchday_insights` in place** — replace its internals to read from
   `mart_momentum__team` (same-layer `ref()`, deliberate — documented in `layering.md`).
   Self-join home + away rows on `fixture_sk`; pivot to wide `home_`/`away_` format.
   Keep all existing output column names so Pages workflow and `index.html` need no changes.
   Additional joins same as today: `mart_team_season` for `league_rank`,
   `dim_team` for logos, `fct_fixture` for metadata not in the momentum mart.
   Drop `shot_share_recent`, `points_capture_recent`, raw sum columns — not rendered in UI.

2. **Extend `scripts/check_layer_contract.py`** — enforce the full cross-layer rule:
   - `staging`: add check that no `ref(...)` call exists (staging reads only from `source()`)
   - `core`: add check that no `ref('mart_*')` call exists
   Update `layering.md` CI table to mark both as enforced.

3. **Delete old intermediate + mart models** once step 1 is verified:
   - `dbt_project/models/4_intermediate/domestic_league/matchday/` (all 8 files)
   - `dbt_project/models/4_intermediate/world_championship/wc/int_wc__matchday_team_form_metrics.sql`
   - `dbt_project/models/5_marts/domestic_league/mart_matchday_insights_bl1_relegation.sql`
   - `dbt_project/models/5_marts/world_championship/mart_matchday_insights_wc.sql`
   - `mart_matchday_player_insights` — retire (confirm no other consumer first)
   - Remove vars from `dbt_project.yml`: `bl1_relegation_round_names`,
     `bl2_playoff_round_names`, `l1_relegation_round_names`

**Column contract for refactored `mart_matchday_insights` (must match `index.html`):**
- `home_`/`away_` prefixed, drop `_recent` suffix from ratio columns
- Fixture metadata: `fixture_sk`, `league_code`, `league_name`, `season_api_year`,
  `kickoff_datetime`, `fixture_date`, `round_name`, `upcoming_round_order`,
  `upcoming_matchday_fixture_count`
- Teams + logos: `home_team_sk/name/logo_url`, `away_team_sk/name/logo_url`
- Standings: `home_league_rank`, `away_league_rank` (from `mart_team_season`)
- Form: `home_form_games_played`, `away_form_games_played` (= `games_in_window`)
- Points: `home_points_won_sum_form`, `away_points_won_sum_form` (= `points_won`)
- Ratios ×11 per side: `goals_per_match`, `goals_against_per_match`, `shots_per_match`,
  `shot_accuracy`, `danger_zone_ratio`, `finishing_efficiency`, `passes_per_match`,
  `pass_accuracy`, `corner_kicks_per_match`, `corners_conceded_per_match`, `save_ratio`

**WC validation deferred to #326** — old WC mart was cumulative (W2), not comparable
to new W1 mart. Validate W2 accuracy when building the season-to-date builders.

## Do NOT
- Do **not** put window suffixes in metric IDs (`_recent`, `_pretournament`, etc.).
- Do **not** add descriptions/tests to `mart_matchday_insights`, `_wc`, or
  `mart_matchday_player_insights` — they are retired in #321.
- Do **not** use dbt MetricFlow / Semantic Layer — use the catalogue **seed**.
- Do **not** infer season boundaries from dates or status flags — use `season_api_year`.
- Do **not** start coding before restating the spec and getting approval.
- Do **not** delete old intermediate models before `mart_matchday_insights` is
  refactored and verified — deleting the chain first breaks the live UI.
- Do **not** add `shot_share_recent` or raw sum columns to the refactored mart —
  they are not rendered in the current UI.
- **Read `project_metrics_context_model.md` memory AND the updated issue body before
  any build.** Previous chats drifted by skipping one or both.

## Conventions reminder
- Bash for all commands; branch from main before writing any file.
- `validate-local` + `sqlfluff lint models/...` before pushing.
- Issue **body** is the contract — if it's not fully specified there, stop and ask.
