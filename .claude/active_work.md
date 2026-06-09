# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-09 (#326 PR #350 + #352 player-pipeline-rehab MERGED; main healthy, tree clean, no open PRs. Next: remaining surfaces #323/#324/#325.)_

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
- ✅ **#321 merged** (PR #339) — de-hardcoding cut-over + a real correctness fix:
  - `mart_matchday_insights` refactored to read from `mart_momentum__team` (same-layer
    ref, documented in `layering.md`). Retired the old `int_matchday__*`/`int_wc__*` chain,
    the BL1-relegation + WC variant marts, `mart_matchday_player_insights`, BL1/BL2/L1
    round vars, 4 stale tests, the metric-consistency macro. `mart_team_season` +
    `int_team_season__full_season_metrics` rerouted to `int_legs__team_match`.
  - `check_layer_contract.py` now enforces the full cross-layer rule (staging no `ref()`;
    core no `ref('mart_*')`).
  - **Coverage-window fix:** cross-competition expansion exposed that momentum ratios
    mixed a full-window numerator with a partial-coverage denominator (sparse stats in
    KL1/VL/MLS → finishing_efficiency 267%). Same-window rule applied: num & denom over
    the same game set, null if none. Per-match stat rates ÷ `games_with_team_stats`,
    player rates ÷ `games_with_player_stats`. Verified on BQ: 0 rows with ratio > 1.
  - **save_ratio reverted** to `saves / (saves + goals_against)` (self-bounding, the
    agreed definition); #320 had silently changed it to `saves / opponent_shots_on_goal`.
    `metric_catalogue.csv` updated to match (consistent with player `save_pct`).
- 🧹 **Branch cleanup (2026-06-06)** — all merged feature branches deleted, local + remote.
- ✅ **#345 merged** — CI fix: `freshness_check` tests now excluded via the `downstream`
  selector in `selectors.yml` (dbt ignores CLI `--exclude` when `--selector` is given, so
  the exclusion had to live in the selector). These tests assert live-data freshness and
  must run only after ingestion (scheduled `dq` selector), never in PR CI. This was the
  real cause of #342's red data-build — NOT the standings work (a transient: J1 matches
  live at last ingest tripped `assert_fct_fixture_no_stale_live`).
- ✅ **#322 merged** (PR #342) — generic standings mart, CI green after #345.
  - Upstream fix: captured true group identity `$.group` → `group_name` (was dropped);
    `fct_standings` grain now `(league, season, team, group_name)`; split-season leagues
    no longer collapse arbitrarily. `group_description` kept as zone annotation only.
  - `mart_standings` (5_marts/shared/, view): generic — league tables + group tables in
    one model; also serves club home-league context via `competition_type='domestic_league'`
    filter. Verified on BQ: PD clean 1..N; AFCCL East/West with rank restarting per group.
- ✅ **#343 merged** (PR #348) — phase-relevant `league_rank` from `mart_standings`.
  - `league_rank` = team's rank in the table of the **fixture's own competition+season**
    (join `mart_standings` on `(team_sk, season_sk)` — season_sk scopes to the competition;
    NO competition_type filter). Domestic league → league table; WC/CL group → group table.
  - Shown only where a single round-robin table applies: `standings_unique` CTE
    (`qualify count(*) over (team_sk, season_sk) = 1`) → overlapping-table leagues
    (Argentina: Apertura group + Anual + Promedios) get NULL; knockout fixtures get NULL
    via new generic macro `macros/is_knockout_round.sql`.
  - Also coalesced `form_games_played` / `points_won_sum_form` to 0 (same mart) — #320's
    momentum-emits-no-row design left them null on a LEFT JOIN and tripped not_null tests.
  - Verified on BQ: grain unique; single-table league ranks match the old values; APD &
    knockout → null; national/continental group ranks now populated. dbt build PASS=34.
- 🧹 **Issue housekeeping (2026-06-06)** — closed 9 stale issues: #320/#321/#322 (merged,
  never auto-closed) + 6 CI-failure auto-issues (#344/#340/#338/#334/#330/#315).
- ✅ **#326 merged** (PR #350) — W2 season-to-date (season-bounded). Builders
  `int_season_to_date__team/__player` (cumulative; carry round_order+match_number for the
  deferred YoY); marts `mart_season_to_date__team/__player` (grain (upcoming_fixture, team
  [/player]); prev-season fallback; same ratios/coverage rules as momentum). Deferred to
  own follow-ups: national qualifier-campaign W2 + WC-before→qualifier fallback; the full
  year-over-year comparison surface.
- ✅ **#352 merged** — player-pipeline rehabilitation (the empty player fact was masking
  layers of DQ debt; turning it on surfaced + fixed all of them):
  - **Self-heal incremental trap**: all 3 fanout facts (`fct_fixture_player_stats`,
    `_team_stats`, `_event`) used `raw_ingested_at > (select max … from {{this}})`, which on
    an EMPTY table is `> NULL` = never true → stuck empty forever. Now
    `> coalesce(max, '1970-01-01')` so an empty table self-heals. + `assert_fanout_facts_not_empty`.
  - **Dropped `player_id = 0`** API placeholder (base filter + null event FK) — fixed 68
    grain dupes + 617 orphans.
  - **Completed `dim_player`**: `base_apif__players` now unions squad (/players) + match
    (fixture_players) + event players — 7,440 match-only players had no dim row.
  - **Clamped impossible source values** in `base_apif__fixture_players`:
    passes_accuracy_percent→[0,100] (API gave up to 191%), dribbles_success≤attempts.
  - One-time **full-refresh** of `core.fct_fixture_player_stats` (Rami-authorized) to purge
    legacy bad rows the incremental couldn't delete. Player surfaces (W1+W2 player marts)
    are now LIVE with valid referential integrity. Final CI run green.
- 📌 **Pending task chip** — remove orphaned macros left by #321 (`bl1/bl2/l1_*_round_names`,
  likely `domestic_league_codes_in_clause`) + the docs that mention them. Separate scope.

## Local env note (not code)
`~/.dbt/profiles.yml` was overwritten by another project (now a `dbt_analytics` duckdb
profile, not `football_data_pipeline`). Local dbt commands fail until restored. Workaround
used this session: `--profiles-dir` pointing at a temp dir with the bigquery oauth profile
(project `football-data-pipeline-gcp`, dataset `dbt_analytics`, EU). CI is unaffected.

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

### 1. Remaining epic #317 surfaces (each its own design pass) ← NEXT
#323 per-fixture stats mart, #324 team profile, #325 player profile. Each needs its own
design discussion + restate-spec-before-coding. Player surfaces (#325, and the player
half of #323) are now unblocked — the player fact is live with valid integrity (#352).

### 2. Deferred follow-ups (open issues when picked up)
- **National qualifier-campaign W2** (multi-season, no season cap) + **WC-before→qualifier
  fallback** (`wc_supporting_league_codes`). Split out of #326.
- **Year-over-year comparison surface** (two seasons aligned by matchday). The
  season-to-date builders already carry `round_order`/`match_number` for it.

### Loose ends (small, optional)
- Orphaned-macro cleanup from #321 (task chip pending — see status above).
- #160 (WC group letters in UI) is now cheap: `mart_standings.group_name` carries the
  real group identity.

## Do NOT
- Do **not** put window suffixes in metric IDs (`_recent`, `_pretournament`, etc.).
- Do **not** use dbt MetricFlow / Semantic Layer — use the catalogue **seed**.
- Do **not** infer season boundaries from dates or status flags — use `season_api_year`.
- Do **not** start coding before restating the spec and getting approval.
- Do **not** mix a full-window numerator with a partial-coverage denominator in any
  ratio — numerator and denominator must cover the **same** set of games; null when none.
  (This is the #321 coverage bug; the rule is now in `metrics_context_model` thinking and
  guarded by [0,1] range tests on `mart_momentum__team`.)
- Do **not** change a metric definition without flagging it against the live/old
  definition (the save_ratio drift in #320 went unreviewed — don't repeat).
- Do **not** show a standing/league_rank where it isn't a single round-robin table for
  the fixture's own competition (locked in #343): null for knockout rounds
  (`is_knockout_round`) and for overlapping-table leagues where a team has >1 section that
  season (e.g. Argentina). Standings are only meaningful for league/group phases.
- Do **not** "fix" a failing DQ test by lowering it to `warn` — fix the data at source
  (locked #352: completed dim_player, clamped impossible values, dropped placeholder ids).
- Do **not** trust a green data-build on an EMPTY table — tests pass trivially on 0 rows.
  An empty core fact is a red flag (`assert_fanout_facts_not_empty` now guards the fanout
  facts). When turning a dormant table back on, expect dormant DQ debt to surface.
- Remember incremental facts retain old rows: a source-side filter/clamp only affects NEW
  inserts; existing bad rows need a **full-refresh** (CI runs incremental, so a one-time
  full-refresh of the affected fact is required to deploy such a fix).
- **Read `project_metrics_context_model.md` memory AND the issue body before any build.**

## Conventions reminder
- Bash for all commands; branch from main before writing any file.
- `validate-local` + `sqlfluff lint models/...` before pushing.
- Issue **body** is the contract — if it's not fully specified there, stop and ask.
