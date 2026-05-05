# Multi-competition pipeline architecture plan

**Status:** Step 1 ingestion fixes merged, re-run pending quota reset. Step 2 not started.  
**Last updated:** 2026-05-05

---

## Goal

Make it easy and straightforward to add any new league/competition. Adding a new competition should require:
1. One entry in `docs/competition_registry.yml`
2. One new mart file (`mart_matchday_insights_{league_code}.sql`)
3. Zero changes to shared intermediate or core models

---

## Ingestion fixes merged (2026-05-05)

- **PR #36**: `current_season` threaded from registry through ingestion — WC uses season 2026 correctly
- **PR #37**: This architecture plan document
- **PR #38**: Stats fetch always attempted for finished fixtures; stale staging model reference in CI trust script fixed
- **PR #39**: All 7 qualifier leagues (WCQEU, WCQAF, WCQCA, WCQSA, WCQAS, WCQIP, WCQOC) made first-class competitions — ingested through the standard pipeline, same level of detail as BL1
- **PR #40**: Fanout gate fixed — finished fixtures always enter the fanout loop for statistics regardless of reference season coverage flags (was silently skipping WC 2022 and WCQEU stats)

## Ingestion status after last run (2026-05-05, quota exhausted mid-run)

- BL1: complete ✓ (3,056/3,056 finished fixtures, all endpoints)
- WC: fixtures and fanout complete except FIXTURE_STATISTICS (72/128 — will be fixed on next run with PR #40)
- WCQEU: fixtures complete (741), lineups/events/players/predictions complete (740/740), FIXTURE_STATISTICS 0/740 (will be fixed on next run)
- WCQAF, WCQCA, WCQSA, WCQAS, WCQIP, WCQOC: 0 fixtures — quota exhausted before they ran. Will complete on next run.

**Next action: re-run ingestion after daily quota resets.**

## Current state

- `mart_matchday_insights.sql` is BL1-only (line 38: `where league_code = 'BL1'`), exported to the web app — **must not break**
- All form logic (~400 lines) is embedded in the mart — no intermediate layer
- Known metric bugs (not yet fixed):
  - `dense_rank()` on `round_order desc` gives 5 matchdays not 5 games — postponed rounds eat slots
  - `coalesce(stat, 0)` deflates averages when stats are absent
  - Previous-season fallback `form_season_api_year - 1` is domestic-league-only; wrong for WC (calendar year)
- One intermediate model exists (`int_apif__raw_ingestion_spread`) — ingestion monitoring, not business logic
- Raw table naming convention: `RAW_APIF_{LEAGUE_CODE}_{ENDPOINT}` (provider first, then league code)

---

## Execution order

### Step 1 — Verify WC ingestion (prerequisite)

Confirm these raw tables are populated after the ingestion run:

| Table | Expected rows |
|---|---|
| `RAW_APIF_WC_FIXTURES` | WC 2026 fixtures |
| `RAW_APIF_WC_TEAMS` | WC participant teams |
| `RAW_APIF_WC_LEAGUES` | WC league metadata |
| `RAW_APIF_WC_QUALIFIER_FIXTURES` | UEFA/CAF/CONCACAF/CONMEBOL/AFC/OFC qualifier fixtures |

If any are empty: re-run ingestion from the worktree with `API_FOOTBALL_INCLUDE_IN_PROGRESS=1`.

### Step 2 — Expand core layer to include WC + qualifier data

**No mart changes in this step.**

Expand staging/base/core models so WC and qualifier data flow through `fct_fixture`, `dim_team`, `dim_league`, `dim_competition_season`.

Checklist:
- [ ] Add staging models for `RAW_APIF_WC_FIXTURES` → `stg_apif__wc_fixtures.sql`
- [ ] Add staging for `RAW_APIF_WC_QUALIFIER_FIXTURES` → fan out by `queried_league_id` to per-qualifier staging (WCQEU, WCQAF, WCQCA, WCQSA, WCQAS, WCQIP, WCQOC)
- [ ] Expand `base_apif__fixtures.sql` (UNION ALL) to include WC + all qualifier staging models
- [ ] Expand `dim_team` to include WC teams
- [ ] Expand `dim_league` to include WC + qualifier league rows
- [ ] Expand `dim_competition_season` to include WC 2026 (calendar year, no split)
- [ ] Expand `fct_fixture` to remove BL1-only filter and include WC + qualifier fixtures
- [ ] Add CI test: `assert_fct_fixture_all_active_competitions_present.sql` — every `league_code` in the registry with status `active` or `in_progress` must have at least one row in `fct_fixture`

> **Risk:** `fct_fixture` expansion touches the BL1 data path. Run `assert_fct_fixture_finished_goals_not_null` and `assert_fct_fixture_goals_plausible` after this step before merging.

### Step 3 — Intermediate layer (new models)

> **Status: DRAFT — not yet approved. Needs review before implementation.**

Two new models in `dbt_project/models/4_intermediate/api_football/`:

#### `int_apif__team_form.sql`

Single source of form computation for all competitions. Replaces embedded logic in `mart_matchday_insights`.

Design decisions (to be confirmed):
- **5 games, not 5 matchdays**: `row_number()` ordered by `fixture_date desc` (or `fixture_id desc`), not `dense_rank()` on `round_order`
- **Season boundary**: `where season_api_year = <reference_season>` — no cross-season mixing
- **No `coalesce(stat, 0)` on averages**: use `avg(stat) filter (where stat is not null)`; null rendered as "—" in UI
- **Form source dispatch by `league_code`**:
  - BL1: form from `league_code = 'BL1'` fixtures only
  - WC pre-group-stage: form from qualifier `league_code` rows (WCQEU, WCQAF, etc.)
  - WC group stage onward: form from `league_code = 'WC'` fixtures
  - Dispatch condition: `group_stage_started` flag derivable from `fct_fixture` (any WC fixture with `round` matching group stage and status FT/AET)
- **Previous-season fallback** (< 5 games in current season):
  - Domestic leagues (split year): `season_api_year - 1` (same `league_code`)
  - Calendar-year tournaments (WC): fallback to qualifier window, not prior WC
  - Controlled by `season_type` from `dim_competition_season`

Output: one row per `(league_code, team_id, as_of_fixture_id)` with form metrics.

#### `int_apif__fixture_enriched.sql`

Enriched fixture rows joining `fct_fixture` → `dim_team` (home/away) → `dim_league` → `dim_competition_season`.

- No league filter — covers all competitions
- Replaces repeated join boilerplate in every mart

Output: one row per fixture with dimension attributes denormalized.

### Step 4 — Intermediate-layer tests

Add before building any mart:

| Test | Assertion |
|---|---|
| `assert_team_form_max_5_games.sql` | No team has > 5 form rows for any reference fixture |
| `assert_team_form_same_season_only.sql` | All form fixtures share `season_api_year` with reference fixture |
| `assert_team_form_no_zero_avg_when_no_stats.sql` | `avg_shots` etc. are null, never 0, when no stat rows exist |
| `assert_fixture_enriched_no_missing_league_code.sql` | Every row in `int_apif__fixture_enriched` has non-null `league_code` |

Seed test: known 6-game sequence for one BL1 team → assert only 5 most recent appear in form output.

### Step 5 — WC mart (new file, does not touch BL1 mart)

`mart_matchday_insights_wc.sql`:

- Selects from `int_apif__fixture_enriched` filtered to `league_code = 'WC'`
- Joins `int_apif__team_form` with form-source logic for WC
- **Same column contract as `mart_matchday_insights`** so web app can consume both with the same query shape
- Add test: `assert_mart_wc_column_contract_matches_bl1.sql`

### Step 6 — Wire WC mart to web app

- Web app gets a competition selector (BL1 / WC)
- Both marts expose identical column names; selector is a filter parameter
- BL1 tab must be regression-tested before this ships

### Step 7 — Migrate BL1 mart to intermediate models

Only after WC mart is validated and live.

1. Rewrite `mart_matchday_insights` to select from `int_apif__team_form` + `int_apif__fixture_enriched`
2. Keep `where league_code = 'BL1'` — intentional, not a bug
3. Drop 400-line embedded form SQL
4. Run full regression: BL1 numbers must match pre-migration output exactly (or document intentional corrections)

This is the only point where the live BL1 web app is at risk. Do not merge until all tests pass and numbers are verified.

### Step 8 — Adding any new competition (repeatable pattern)

1. Add entry to `docs/competition_registry.yml`
2. Run ingestion — raw tables auto-created
3. Staging + base union picks up new `league_code` automatically
4. `int_apif__fixture_enriched` and `int_apif__team_form` pick it up automatically
5. Create `mart_matchday_insights_{league_code}.sql` — selects from intermediate with `where league_code = '...'`
6. Add competition card to web app

Steps 3–4 require zero dbt model changes.

---

## Open questions / not yet decided

- **Step 3 form source dispatch**: exact SQL condition for "WC group stage has started" — needs review from analytics engineer
- **Step 3 previous-season fallback for WC**: qualifier window boundary dates — needs review
- **Step 6 web app competition selector**: frontend design not planned here
- **Step 7 migration timing**: how to validate BL1 regression without breaking the live export

---

## Branch / PR plan

| Step | Branch name | PR |
|---|---|---|
| 1–2 | `feature/core-multi-competition` | TBD |
| 3–4 | `feature/intermediate-team-form` | TBD |
| 5 | `feature/mart-wc-matchday-insights` | TBD |
| 6 | `feature/web-app-competition-selector` | TBD |
| 7 | `refactor/bl1-mart-use-intermediate` | TBD |
