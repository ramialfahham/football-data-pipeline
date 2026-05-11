# Multi-competition pipeline architecture plan

**Status:** Step 1 complete. Step 2 architecture decided (manual-UNION base + CI guarantee + core source-agnostic); execution split into 6 endpoint-surface PRs (2.1 through 2.6). Step 3 onwards still draft.  
**Last updated:** 2026-05-10

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

## Subsequent architectural changes (2026-05-06 → 2026-05-10)

These changed inputs and constraints to Step 2 and need to be reflected in the plan:

- **PR #48 — Global completeness-driven fanout**: priority queue across all competitions, with `history_seasons` per competition. Combined with PR #39, **each qualifier confederation is now a first-class competition with its own per-confederation raw tables** (`RAW_APIF_WCQEU_*`, `RAW_APIF_WCQAF_*`, etc.). The earlier aggregate `RAW_APIF_WC_QUALIFIER_FIXTURES` table is no longer written and is stale since 2026-05-05.
- **PR #49 — Catalog guard**: `/leagues` writes only when the API returns non-empty `response`, preventing daily-quota errors from wiping valid leagues data via WRITE_TRUNCATE.
- **PR #51 — `mart_team_season` rank fix**: short-term workaround at the mart layer (use latest `snapshot_valid_from` for dedup) so the matchday-preview UI shows correct Tabellenplatz.
- **PR #52 — Standings snapshot removed**: `snap_apif_d1_standings` deleted. `fct_standings` now sources from `base_apif__bl1_standings` (regular table dedup), not from an SCD2 snapshot. There is currently no snapshot anywhere in the project.
- **PR #53 — Tiered completeness gate + run summary**: scheduled workflow hard-fails only when an `active` competition is incomplete; `in_progress` competitions warn and stay green. Every run renders a per-competition coverage table to `$GITHUB_STEP_SUMMARY`. This is the always-on observability for the pipeline.
- **PR #56 — Injuries removal**: the entire injury surface (ingestion call, `merge_injuries_envelope`, dbt sources, staging models, `fct_injury` mention in deferred-fact list) is deleted. Injuries are no longer ingested for any competition and the architecture should not reference them.
- **Diagnostic scripts** added under `scripts/diagnostics/`: `inspect_raw_payload.py`, `probe_time_travel.py`, `restore_from_time_travel.py`. Used today to restore `RAW_APIF_BL1_LEAGUES` from BigQuery time travel after a quota-induced WRITE_TRUNCATE corruption.

## Ingestion status as of 2026-05-10

| Competition | Finished fixtures | Fanout coverage | Notes |
|---|---|---|---|
| BL1 | 3,056 / 3,056 | ✅ all 5 endpoints 100% | active |
| WC | 128 / 128 | ✅ all 5 endpoints 100% | active |
| WCQEU | 740 / 740 | LINEUPS/EVENTS/PLAYERS/PRED 100%; STATS 99.9% (1 missing) | in_progress |
| WCQAF | 540 / 540 | LINEUPS/EVENTS/PLAYERS/PRED 100%; STATS ~20% (434 missing) | in_progress |
| WCQCA | 330 / 330 | LINEUPS/EVENTS/PLAYERS/PRED 100%; STATS ~55% (148 missing) | in_progress |
| WCQSA | 269 / 269 | LINEUPS/EVENTS/PLAYERS/PRED 100%; STATS 99.3% (2 missing) | in_progress |
| WCQAS | 681 / 681 | LINEUPS/EVENTS/PLAYERS/PRED 100%; STATS ~45% (372 missing) | in_progress |
| WCQIP | 4 / 4 | LINEUPS/EVENTS/PLAYERS/PRED 100%; STATS ~25% (3 missing) | in_progress |
| WCQOC | 18 / 18 | LINEUPS/EVENTS/PLAYERS/PRED 100%; STATS 0% (18 missing) | in_progress |

BL1 and WC are fully complete; qualifier statistics will converge to 100% over additional scheduled runs as the global fanout prioritizes missing fixtures. The completeness target is **0% gap** — any qualifier fixture without statistics is treated as incomplete until backfilled.

## Current state

- `mart_matchday_insights.sql` is BL1-only (`where league_code = 'BL1'`), exported to the web app — **must not break**
- All form logic (~400 lines) is embedded in the mart — no intermediate layer
- Known metric bugs (not yet fixed):
  - `dense_rank()` on `round_order desc` gives 5 matchdays not 5 games — postponed rounds eat slots
  - `coalesce(stat, 0)` deflates averages when stats are absent
  - Previous-season fallback `form_season_api_year - 1` is domestic-league-only; wrong for WC (calendar year)
- One intermediate model exists (`int_apif__raw_ingestion_spread`) — ingestion monitoring, not business logic
- Raw table naming convention: `RAW_APIF_{LEAGUE_CODE}_{ENDPOINT}` (provider first, then league code)
- Each qualifier confederation is its own competition (status `in_progress` in the registry) with its own per-confederation raw tables — there is no aggregate qualifier raw table any more
- No SCD2 snapshots in the project; injuries are not ingested (see PR #52 and PR #56 above)
- Dim layer already covers WC: `dim_league`, `dim_competition_season`, `dim_team` UNION BL1 + WC base models. Qualifier confederations are **not** yet in any dim.
- All fact tables are still BL1-only — they read only from BL1 base models
- WC base models exist for: `_fixtures_next`, `_leagues`, `_teams`. WC base models do not yet exist for: `_standings`, `_fixture_statistics`, `_fixture_events`, `_fixture_players`, `_players`, `_transfers`.

---

## Execution order

### Step 1 — Verify WC ingestion (prerequisite) — DONE

WC and the 7 qualifier confederations are each first-class competitions in the registry, ingested through the standard pipeline with their own per-confederation raw tables.

Per-competition raw tables (BL1 reference shown for comparison; same endpoint suffixes for all):

| League code | Status | Raw tables produced |
|---|---|---|
| `BL1` | active | `RAW_APIF_BL1_FIXTURES_NEXT`, `_LEAGUES`, `_STANDINGS`, `_ROUNDS`, `_TEAMS`, `_TRANSFERS`, `_LINEUPS`, `_FIXTURE_EVENTS`, `_FIXTURE_STATISTICS`, `_FIXTURE_PLAYERS`, `_PREDICTIONS`, `_PLAYERS` |
| `WC` | active | same set, `WC` prefix |
| `WCQEU`, `WCQAF`, `WCQCA`, `WCQSA`, `WCQAS`, `WCQIP`, `WCQOC` | in_progress | same set per confederation, `WCQ<XX>` prefix |

Verify with the diagnostic script when needed:

```bash
python scripts/diagnostics/inspect_raw_payload.py --table RAW_APIF_<league_code>_<entity>
```

Completeness state for these tables is shown in the **Ingestion status as of 2026-05-10** section above.

The aggregate `RAW_APIF_WC_QUALIFIER_FIXTURES` table referenced in the original (2026-05-05) plan is **obsolete and stale** since PR #39 / #48 made each qualifier a first-class competition. The dbt source declaration `raw_apif_wc_qualifier_fixtures` and the staging/base models that read it were removed in Step 2.1 (multi-competition foundation PR).

### Step 2 — Expand core layer to full BL1 parity across all competitions


**Step 2.1 sequencing correction:** The original plan split fixtures (2.1) from leagues/teams (2.6). `fct_fixture` relationship tests require `dim_competition_season`, `dim_league`, and `dim_team` to already include qualifier rows. PR 2.1 therefore bundles the three unified bases (leagues, teams, fixtures_next) with the dim and fixture refactors in one merge unit so BL1 stays green.

**No mart changes in this step.** Scope is data-flow plumbing only; form-source dispatch (qualifiers → WC group stage) is Step 3.

Goal: every fact in `3_core` covers BL1 + WC + 7 qualifier confederations, sourced by the same shape of base model as BL1 uses today. Every dim covers the same 9 competitions.

#### Layer discipline (re-stated)

- **Staging is 1:1 with raw.** One staging model per raw table — JSON unnesting, casting, no UNION ALL, no business logic.
- **Base is the unification point.** UNION ALL across competitions + dedup happens here. **Each endpoint gets exactly one base model** that unions every per-competition staging via explicit `ref()` calls. No per-competition base models.
- **Core consumes base only.** Facts and dims read from a single base per endpoint and never UNION across competitions. Core is source-agnostic.

#### Architectural decision — manual UNION list + CI guarantee (not auto-discovery)

The technical north star (`docs/north_star.md`) documents ingestion + staging + mechanical base `ref()` lines, with no core/mart edits per competition once bases exist for an endpoint. The literal "staging only" reading would force auto-discovery in base (Jinja over `graph.nodes`). I'm deliberately not going that route. Decision and rationale, as senior analytics engineer:

- Each base model lists its component stagings explicitly with `ref()`. Adding a competition means adding one `ref()` line per base — mechanical, ~10 lines total across all bases.
- Singular tests (`assert_base_*_covers_active_competition_var.sql`, see test table below) fail if any `league_code` in `vars.active_competition_league_codes` is missing from a unified base; `scripts/check_registry_var_sync.py` keeps that var aligned with the registry (`active` / `in_progress`).
- **Why not auto-discovery**: dbt's strength is explicit `ref()` lineage — visible in `dbt docs`, the lineage graph, and `dbt --select +model` selectors. `graph.nodes` enumeration hides those edges from dbt's graph and is a rare pattern that's harder for future contributors to read. Adding a competition is quarterly cadence, not daily — the cost of editing ~10 mechanical `ref()` lines is negligible compared to the cost of debugging Jinja-graph magic the one time it goes wrong.
- **The north star's spirit is preserved**: zero changes to **core, intermediate, or marts** when adding a competition once unified bases cover that endpoint. Base edits remain mechanical and CI-guaranteed.

For each endpoint surface listed below, the work pattern is identical:

1. Declare per-confederation raw sources in `sources.yml` (21 table entries for leagues, teams, fixtures_next per WCQ code)
2. Add a WC staging model if missing (`stg_apif__wc_<endpoint>`)
3. Add 7 per-confederation staging models (`stg_apif__wcqeu_<endpoint>`, etc.)
4. Add or extend the base model so it UNION ALLs BL1 + WC + 7 qualifiers and dedupes
5. Expand the corresponding fact (drop BL1-only references)
6. Add the active-competitions presence test for that fact

#### Per-endpoint scope

| Endpoint surface | Stagings (9 total per endpoint when complete) | Base model | Core consumers (refactored to read single base) |
|---|---|---|---|
| Fixtures | BL1 ✓, WC ✓, 7 qualifiers (new) | `base_apif__fixtures_next` (replaces per-competition bases) | `fct_fixture` |
| Standings | BL1 ✓, WC (new), 7 qualifiers (new) | `base_apif__standings` (replaces `base_apif__bl1_standings`) | `fct_standings` |
| Fixture statistics | BL1 ✓, WC (new), 7 qualifiers (new) | `base_apif__fixture_statistics` (new) | `fct_fixture_team_stats` |
| Fixture events | BL1 ✓, WC (new), 7 qualifiers (new) | `base_apif__fixture_events` (new) | `fct_fixture_event` |
| Fixture players | BL1 ✓, WC (new), 7 qualifiers (new) | `base_apif__fixture_players` (new) | `fct_fixture_player_stats` |
| Teams | BL1 ✓, WC ✓, 7 qualifiers (new) | `base_apif__teams` (replaces per-competition bases) | `dim_team` |
| Players | BL1 ✓, WC (new), 7 qualifiers (new) | `base_apif__players` (new) | `dim_player` |
| Transfers | BL1 ✓, WC (new), 7 qualifiers (new) | `base_apif__transfers` (new) | `fct_transfer` |
| Leagues | BL1 ✓, WC ✓, 7 qualifiers (new) | `base_apif__leagues` (replaces per-competition bases) | `dim_league`, `dim_competition_season` |
| Lineups | BL1 ✓, WC (new), 7 qualifiers (new) | `base_apif__lineups` (new) | (no fact yet — feeds Step 3 form computation) |
| Predictions | BL1 ✓, WC (new), 7 qualifiers (new) | `base_apif__predictions` (new) | (no fact yet — feeds Step 3) |

Total work for Step 2:
- ~63 new per-confederation staging models (7 qualifiers × 9 endpoints, minus those already existing)
- ~8 new WC stagings (endpoints WC doesn't have yet)
- 11 single-union base models (replace existing per-competition bases; add new for endpoints without bases)
- 6 fact and 3 dim refactors — each reads exactly one base, no UNION in core
- The CI tests below

**Core source-agnosticism**: after Step 2, every model in `3_core/` reads from a single `base_apif__<endpoint>` and contains zero `union_all` macros or per-competition `ref()` calls. This is the test of whether the principle is met.

#### Cleanup tasks (part of Step 2)

- [x] Remove `raw_apif_wc_qualifier_fixtures` from `sources.yml` (no longer written)
- [x] Delete `stg_apif__wc_qualifier_fixtures.sql` and `base_apif__wc_qualifier_fixtures.sql`
- [x] Drop the BQ table `RAW_APIF_WC_QUALIFIER_FIXTURES` via `scripts/drop_raw_apif_wc_qualifier_fixtures.py` (run `--apply` after merge)
- [x] Drop the `--exclude stg_apif__wc_qualifier_fixtures base_apif__wc_qualifier_fixtures` flags from both workflow files

#### Tests required for Step 2 (added in CI)

| Test | Assertion |
|---|---|
| `assert_base_leagues_covers_active_competition_var.sql` (and teams / fixtures_next variants) | Every `league_code` in `vars.active_competition_league_codes` has ≥ 1 row in the unified base (must match registry; enforced by `check_registry_var_sync.py`). **Manual-UNION guarantee.** |
| `check_layer_contract.py` | Fails if any `3_core/*.sql` contains `union_all(` — core reads a single base per endpoint. |
| `assert_fct_fixture_covers_active_competition_var.sql` | Every var `league_code` has ≥ 1 row in `fct_fixture` |
| `assert_fct_standings_all_active_competitions_present.sql` | Same shape, for standings |
| `assert_fct_fixture_team_stats_all_active_competitions_present.sql` | Same shape, for stats |
| `assert_fct_fixture_event_all_active_competitions_present.sql` | Same shape, for events |
| `assert_fct_fixture_player_stats_all_active_competitions_present.sql` | Same shape, for player stats |
| `assert_dim_team_all_active_competitions_present.sql` | Every team appearing in any fact has a `dim_team` row |
| `assert_dim_player_all_active_competitions_present.sql` | Same shape, for players |
| `assert_dim_league_all_active_competitions_present.sql` | Every `league_code` in registry → row in `dim_league` |

> **Risk:** Expanding the facts touches the BL1 data path. After each endpoint surface PR, re-run the existing BL1 trust diagnostics (`assert_fct_fixture_finished_goals_not_null`, `assert_fct_fixture_goals_plausible`, `data_trust_fixture_stats.py`) and verify the matchday-preview JSON export for BL1 is unchanged before merging.

> **Completeness gating:** Qualifier statistics are still backfilling (see ingestion status table). The tiered completeness gate (PR #53) keeps the scheduled workflow green while backfill converges. Step 2 fact expansions surface the partial data, but the matchday-preview UI will not consume WC / qualifier facts until Steps 5+ wire them in.

### Step 3 — Intermediate layer (new models)

> **Status: DRAFT — not yet approved. Needs review before implementation.**

Two new models in `dbt_project/models/4_intermediate/api_football/`:

#### `int_apif__team_form.sql`

Single source of form computation for all competitions. Replaces embedded logic in `mart_matchday_insights`.

Design decisions (to be confirmed):
- **5 games, not 5 matchdays**: `row_number()` ordered by `fixture_date desc` (or `fixture_id desc`), not `dense_rank()` on `round_order`
- **Season boundary**: `where season_api_year = <reference_season>` — no cross-season mixing
- **No `coalesce(stat, 0)` on averages**: use `avg(stat) filter (where stat is not null)`; null rendered as "—" in UI
- **Form source dispatch by `league_code` (per-team, per-fixture)**:
  - BL1 (and other domestic leagues): form from last 5 fixtures in same `league_code` + `season_api_year`
  - WC, pre-tournament for this team (team has not yet played its first WC 2026 fixture with status FT/AET/PEN): form computed from **all** qualifier fixtures the team participated in across qualifier `league_code`s (WCQEU, WCQAF, WCQCA, WCQSA, WCQAS, WCQIP, WCQOC). Not last 5 — every qualifier match the team played in this WC's qualifier window.
  - WC, after this team's first WC fixture: form from last 5 `league_code = 'WC'` fixtures only; qualifier data dropped.
  - Dispatch is **per-team-per-fixture**, not tournament-wide. Different teams enter group stage at different match-days; each team's form switches independently.
- **Previous-season fallback** (< 5 games in current season, applies only to leagues; WC uses qualifier window instead):
  - Domestic leagues (split year): `season_api_year - 1` (same `league_code`)
  - Calendar-year tournaments (WC): no previous-season fallback; the pre-tournament qualifier window covers it
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
3. Add per-endpoint staging models (`stg_apif__<league_code>_<endpoint>.sql`) — 1:1 with raw, JSON cast only. ~10 stagings for full BL1 parity.
4. Add one `ref()` line per base model (`base_apif__<endpoint>`) to include the new staging in the UNION. Singular tests `assert_base_*_covers_active_competition_var` flag a missing `league_code` in a base.
5. Create `mart_matchday_insights_{league_code}.sql` — selects from intermediate with `where league_code = '...'`
6. Add competition card to web app

Steps 3–4 are mechanical edits with CI guarantees. **Zero changes to `3_core`, `4_intermediate`, or any other `5_marts` model.**

---

## Open questions / not yet decided

- **Step 3 form source dispatch implementation**: per-team-per-fixture dispatch (qualifier vs WC) is decided; the exact SQL — likely a CASE-WHEN on "has this team played any WC fixture with status FT/AET/PEN as of the reference fixture's date?" — needs writing during Step 3 implementation
- **Step 3 qualifier window boundary**: which dates count as "qualifier window for WC 2026" — needs analytics engineer to set bounds (probably the registry `current_season` years for each WCQ* league)
- **Step 6 web app competition selector**: frontend design not planned here
- **Step 7 migration timing**: how to validate BL1 regression without breaking the live export

**Decided in this update (no longer open):**
- Base architecture: manual UNION list with `assert_base_*_covers_active_competition_var` singular tests + `scripts/check_registry_var_sync.py`, not auto-discovery
- Existing per-competition bases (`base_apif__bl1_*`, `base_apif__wc_*`) are replaced by single `base_apif__<endpoint>` models as part of Step 2; core stops UNIONing
- Pre-tournament WC form uses *all* qualifier matches per participant, not last 5

---

## Branch / PR plan

Step 2 is too large for one PR. Split by endpoint surface so each PR's blast radius is bounded and the BL1 data path is regression-tested incrementally:

| Step | Branch name | Scope |
|---|---|---|
| 2.1 | `feature/core-multi-competition-foundation` | Fixtures plus dim foundation (bundled): unified bases leagues/teams/fixtures_next, core single-base refs, WCQ stagings and sources, qualifier aggregate removal, registry/var sync and singular tests. |
| 2.2 | `feature/core-standings-multi-competition` | Standings: WC + 7 qualifier stagings + union base + `fct_standings` expansion + test |
| 2.3 | `feature/core-fixture-stats-multi-competition` | Fixture statistics: same shape |
| 2.4 | `feature/core-fixture-events-multi-competition` | Fixture events: same shape |
| 2.5 | `feature/core-fixture-players-multi-competition` | Fixture players + `dim_player` expansion |
| 2.6 | `feature/core-transfers-lineups-predictions-multi-competition` | Transfers, lineups, predictions (teams/leagues/fixtures covered in 2.1). |
| 3–4 | `feature/intermediate-team-form` | Per the draft Step 3 below — needs approval before starting |
| 5 | `feature/mart-wc-matchday-insights` | Per Step 5 below — needs Step 2–4 complete |
| 6 | `feature/web-app-competition-selector` | Per Step 6 below |
| 7 | `refactor/bl1-mart-use-intermediate` | Per Step 7 below — only after Step 5 is live and validated |
