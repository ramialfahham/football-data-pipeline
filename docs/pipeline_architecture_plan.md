# Multi-competition pipeline architecture plan

**Status:** Step 1 complete. Step 2 architecture decided (manual-UNION base + CI guarantee + core source-agnostic); execution split into 6 endpoint-surface PRs (2.1 through 2.6). **Step 3 matchday-form rules are locked** — CPO clarifications **2026-05-15** are recorded under **CPO decisions (recorded)**.

**Last updated:** 2026-05-15

## Goal

Make it easy and straightforward to add any new league/competition. Adding a new competition should require:
1. One entry in `docs/competition_registry.yml`
2. One new mart file (`mart_matchday_insights_{league_code}.sql`)
3. **Registry-driven extensions** to shared **`int_matchday__*`** intermediates where the form/upcoming-round behaviour is shared; **no** ad hoc business logic in `3_core`. (Core schema changes are separate gated PRs when new facts are introduced.)

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
- **PR #52 — Standings snapshot removed**: `snap_apif_d1_standings` deleted. `fct_standings` now sources from unified `base_apif__standings` (regular table dedup across competitions), not from an SCD2 snapshot. There is currently no snapshot anywhere in the project.
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

- `mart_matchday_insights_bl1.sql` is BL1-only (`where league_code = 'BL1'`); `mart_matchday_insights.sql` is a thin view for the stable export name — **must not break**
- Form and matchday spine live in `int_matchday__*` models; the mart joins those intermediates with `mart_team_season`
- Known gaps vs **Step 3 + CPO decisions** — implementation PR will close:
  - Matchday-based window vs **games** + **full previous season before current season starts**
  - `coalesce(stat, 0)` vs **null** numerics + **“Not provided”** copy for optional API gaps (glossary/UI)
  - WC qualifier-all → five WC legs dispatch not yet in `int_matchday__team_form_metrics`
- Intermediate: `int_pipeline__raw_ingestion_spread` (ingestion monitoring); `int_matchday__*` (fixture denorm, finished legs + stats, upcoming round, team form metrics). **Rule:** `4_intermediate` models must not `ref()` any `mart_*` model.
- Raw table naming convention: `RAW_APIF_{LEAGUE_CODE}_{ENDPOINT}` (provider first, then league code)
- Each qualifier confederation is its own competition (status `in_progress` in the registry) with its own per-confederation raw tables — there is no aggregate qualifier raw table any more
- No SCD2 snapshots in the project; injuries are not ingested (see PR #52 and PR #56 above)
- Dims `dim_league`, `dim_competition_season`, and `dim_team` read unified `base_apif__leagues` / `base_apif__teams` (PR #59 — all registry competitions with staging).
- `fct_fixture` reads `base_apif__fixtures_next` (PR #59). `fct_standings` reads `base_apif__standings` (Step 2.2). Other facts remain BL1-only until their Step 2.x PRs.
- Per-competition bases for leagues, teams, fixtures, and standings are superseded by unified `base_apif__*` models with explicit `ref()` lists; remaining endpoints follow the same pattern in the plan table.

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
| `assert_base_fixture_statistics_covers_active_competition_var.sql` | Every var `league_code` with fixture-statistics coverage has ≥ 1 row in `base_apif__fixture_statistics` |
| `assert_fct_standings_covers_active_competition_var.sql` | Every var `league_code` has ≥ 1 row in `fct_standings` |
| `assert_fct_fixture_team_stats_covers_active_competition_var.sql` | Every var `league_code` with fixture-statistics coverage has ≥ 1 row in `fct_fixture_team_stats` |
| `assert_fct_fixture_event_all_active_competitions_present.sql` | Same shape, for events |
| `assert_fct_fixture_player_stats_all_active_competitions_present.sql` | Same shape, for player stats |
| `assert_dim_team_all_active_competitions_present.sql` | Every team appearing in any fact has a `dim_team` row |
| `assert_dim_player_all_active_competitions_present.sql` | Same shape, for players |
| `assert_dim_league_all_active_competitions_present.sql` | Every `league_code` in registry → row in `dim_league` |

> **Risk:** Expanding the facts touches the BL1 data path. After each endpoint surface PR, re-run the existing BL1 trust diagnostics (`assert_fct_fixture_finished_goals_not_null`, `assert_fct_fixture_goals_plausible`, `data_trust_fixture_stats.py`) and verify the matchday-preview JSON export for BL1 is unchanged before merging.

> **Completeness gating:** Qualifier statistics are still backfilling (see ingestion status table). The tiered completeness gate (PR #53) keeps the scheduled workflow green while backfill converges. Step 2 fact expansions surface the partial data, but the matchday-preview UI will not consume WC / qualifier facts until Steps 5+ wire them in.

### Step 3 — Matchday form & fixture spine (intermediate; design locked)

> **Status: LOCKED — product rules in “Locked rules (CPO-aligned)” + “CPO decisions (recorded)”.** Implement in `dbt_project/models/4_intermediate/matchday/` by evolving **`int_matchday__team_form_metrics`** (and related ints). Older drafts in this file referred to `int_apif__team_form` / `int_apif__fixture_enriched`; those map to **`int_matchday__team_form_metrics`** and **`int_matchday__fixture_denormalized`** (already one row per fixture with core dims).

#### Locked rules (CPO-aligned)

1. **Domestic leagues (`form_source: league_only`, e.g. BL1)**  
   - **Before the competition has started** (no finished league match yet in the **current** `season_api_year` for that `league_code`): compute form from the **entire previous season** — all finished matches for that team in the same `league_code` with the prior season year (`season_type` / split-year rules from `dim_competition_season`).  
   - **After the first finished match of the current season:** use **only** the **current** competition. Rolling window = the **last five finished matches** in that `league_code` + current `season_api_year`, ordered by kickoff (deterministic tie-break). **Until five such matches exist**, include **every** finished match played so far (matchday 1 → one game, matchday 3 → up to three games, etc.). **Never** use `dense_rank()` on `round_order` to fake five slots when postponements leave gaps — the window is **games**, not **matchdays**.

2. **WC (`form_source: supporting_leagues`)**  
   - **Before WC “day 1”** (before the team has any finished **`league_code = 'WC'`** tournament match, relative to the reference fixture’s kickoff): form uses **all** finished qualifier legs for that team across every internal `league_code` listed under the WC’s `supporting_leagues` in **`docs/competition_registry.yml`** (no cap at five).  
   - **After** the team’s first finished WC tournament match (FT / AET / PEN): use **only** `league_code = 'WC'` finished legs — same **up-to-five finished games** rolling rule as domestic (kickoff order, cap at five once enough games exist).

3. **Season boundaries**  
   Do not mix legs across the wrong season year for the path above. `season_type` from `dim_competition_season` / registry drives which `season_api_year` counts as “previous” for split-year leagues.

4. **Missing data — contract vs copy**  
   - **Integrity / must-not-lie:** If the warehouse says a match is finished but **required** facts are missing (e.g. both goals null), **CI must stay red** (existing singular tests; extend only when product defines new hard requirements).  
   - **Optional provider gaps:** When API-Football simply **does not supply** a stat for a leg, **do not** coerce to `0` in rates. Expose **null** in numeric columns and document in **`metric_glossary`** / UI that the rendered label is **`Not provided`** (or equivalent plain language), **not** a numeric zero. The app should not show a bare em dash that reads like “zero”.

5. **Marts stay thin**  
   `mart_matchday_insights_bl1`, future `mart_matchday_insights_wc`, and the **`mart_matchday_insights`** shim: filters, column order, display names only — **no** window or dispatch logic here.

#### Implementation defaults (analytics engineering; revise only via this doc)

- **“Competition started” for domestic** = exists at least one **finished** (FT/AET/PEN) fixture in `fct_fixture` for that `league_code` + current `season_api_year` (with non-null goals per finished-leg int).  
- **First WC tournament match for dispatch** = earliest finished WC leg for the team with `kickoff_datetime <` the reference upcoming fixture kickoff.  
- **Supporting qualifier set** = WC registry `supporting_leagues` → internal `league_code` list actually ingested.

### Step 4 — Intermediate-layer tests

Add or extend before shipping changed JSON to fans:

| Test | Assertion |
|---|---|
| `assert_team_form_max_5_games.sql` | After domestic “competition started”: at most **5** current-season legs in the window per `(fixture_sk, team_sk)`; before start, previous-season path may exceed 5 |
| `assert_team_form_same_season_only.sql` | Legs obey the season / dispatch rule for that path (not a blind `season_api_year = ref.season_api_year` if the spec says otherwise) |
| `assert_team_form_no_zero_avg_when_no_stats.sql` | Rates are **null** when inputs missing — never silent numeric zero; UI/glossary maps optional gaps to **“Not provided”** |
| Fixture grain | Extend existing tests on **`int_matchday__fixture_denormalized`** if new columns are added |

**Seed / scenario test:** six finished games in sequence → only the **five** most recent by kickoff enter the capped window.

### Step 5 — WC mart (new file; does not change BL1)

`mart_matchday_insights_wc.sql`:

- Thin mart: `league_code = 'WC'` on the same upcoming-round + form spine as BL1.
- **Identical column contract to `mart_matchday_insights_bl1`** for the web renderer.
- Singular test: **`assert_mart_wc_column_contract_matches_bl1.sql`**.

### Step 6 — Wire WC to the web app

- Selector (BL1 vs WC) and/or second export; BL1 regression required.

### Step 7 — BL1 behaviour vs legacy numbers

`mart_matchday_insights_bl1` is already structurally thin. After **`int_matchday__team_form_metrics`** matches Step 3, run **full regression** on exported JSON (or document every intentional delta in the PR).

### Step 8 — New competition (repeatable)

1. Registry → ingestion → staging → base `ref()` + coverage tests  
2. `mart_matchday_insights_<league_code>.sql` thin mart

**Scope discipline:** Steps 3–4 touch **`4_intermediate`** and **tests**. **No `3_core` changes** as part of form dispatch. Step 5 **adds** a mart. **`mart_matchday_insights` (shim)** keeps the stable BigQuery name for the exporter.

---

## Open questions (narrow)

- **Optional hard calendar for qualifiers:** Default = **no** extra date cut-out beyond what is already implied by `season_api_year` / ingested facts. Add explicit bounds here only if product requires them.
- **Step 6 UX** lives in product / site repos.

**Already locked:** dispatch rules; “all qualifiers pre-WC”; rolling five in-season; display policy for optional API gaps.

---

## CPO decisions (recorded)

**Source:** Product clarification (conversation, **2026-05-15**). Supersedes the earlier four-question checklist; no further template reply required.

| Topic | Decision |
|-------|----------|
| **Domestic form windows** | Before any finished match in the **current** league season → form from **full previous season** for that team/league. After play starts → **current season only**, **up to the last five finished matches** (fewer early in the season: MD1 → one game, MD3 → up to three, etc.). |
| **WC pre-tournament** | **All** finished qualifier matches for that team across WC-linked qualifier competitions — **not** capped at five. |
| **Missing / optional stats** | **Integrity failures** (e.g. impossible finished row) → **fail pipeline / tests**. **API omitted optional stat** → keep **null** in numeric marts; user-facing copy **`Not provided`** (or equivalent) via **glossary + UI**, not a fake zero. |
| **Sign-off** | The table above is the authoritative Step 3 product contract for implementation PRs. |

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
| 3–4 | `feature/intermediate-team-form` | Implement **locked Step 3** in `int_matchday__*` + tests (per **CPO decisions (recorded)**) |
| 5 | `feature/mart-wc-matchday-insights` | Per Step 5 below — needs Step 2–4 complete |
| 6 | `feature/web-app-competition-selector` | Per Step 6 below |
| 7 | `refactor/bl1-mart-use-intermediate` | Per Step 7 below — only after Step 5 is live and validated |
