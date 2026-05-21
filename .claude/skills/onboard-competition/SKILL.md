---
name: onboard-competition
description: |
  Onboard a new football competition (domestic league or tournament) into the
  football-data-pipeline. Scaffolds 12 dbt staging models, registers sources,
  adds UNION ALL blocks to 5 base models, updates the competition registry +
  active-competition-codes var, and adds the i18n competition label in en/de/fi.

  Use this when a new league_code needs to be onboarded with the same
  pattern as VL / PL / PD / SA / L1 / BL2 / LMX. Do NOT use for WC qualifier
  competitions (WCQ*) — those follow a different shape and are pre-onboarded.
---

# onboard-competition

This skill codifies the league-onboarding recipe that is currently followed
manually each time. It's been validated on the VL → LMX onboardings (#151
Wave 1) and intentionally mirrors the VL template, which is the canonical
reference.

## When to use

The user has provided:

- An API-Football league id (e.g. `253` for MLS, `307` for Saudi Pro)
- A short league code to assign (e.g. `MLS`, `SPL`, `ED`, `LP`)
- The full league name (e.g. `Major League Soccer`)
- Country (e.g. `United States`)
- Season type (`split_year` for European-style Aug→May, `calendar_year` for
  spring-autumn or one-year competitions)
- Current season year (e.g. `2025`, `2026`)

If anything is missing, ask the user. Do not guess league ids — confirm
against `https://v3.football.api-sports.io/leagues?id={id}`.

## When NOT to use

- WC tournament itself or any WCQ* (World Cup qualifier) confederation —
  those are pre-onboarded with a different per-league shape and overlay
  more tournament-specific marts. Do not run this skill against those codes.
- Renaming an existing league. That's a separate workflow involving raw
  table renames, snapshot history, etc.

## Required inputs (collect before starting)

| Input | Example | Validation |
|---|---|---|
| `league_code` | `MLS` | 2–4 uppercase letters, unique vs `docs/competition_registry.yml` |
| `name` | `Major League Soccer` | for registry + UI labels |
| `country` | `United States` | for registry only |
| `provider_league_id` | `253` | integer; verify against API live |
| `season_type` | `split_year` or `calendar_year` | exact lowercase string |
| `current_season` | `2026` | API season identifier |
| `history_seasons` | `1` | default 1; bump to 2 if the league's prior season feeds form fallback |
| `notes` | free text | rationale, e.g. "WC 2026 host coverage for USA + Canada" |

## Procedure

Run these steps in order. After each step, briefly confirm what landed
before moving on. Do not batch multiple steps silently.

### Step 0 — Validate inputs

- Confirm `provider_league_id` against the live API: `GET /leagues?id={id}`
  should return that league. The response's `coverage.fixtures.statistics_players`
  must be `true` for the player insights work to ever apply.
- Confirm `league_code` does NOT already appear in `docs/competition_registry.yml`.

### Step 1 — Branch from origin/main

```bash
cd <repo root or worktree>
git fetch origin main --quiet
git checkout -B feat/onboard-{league_code_lower} origin/main
```

### Step 2 — Scaffold 12 staging files from VL template

Copy each file in `dbt_project/models/1_staging/api_football/vl/stg_apif__vl_*.sql`
to `dbt_project/models/1_staging/api_football/{lc_lower}/stg_apif__{lc_lower}_*.sql`,
performing these case-sensitive substitutions in the content:

- `'VL'` → `'{LEAGUE_CODE}'` (uppercase; preserves the `'LEAGUE_CODE' as league_code` literal)
- `_vl_` → `_{lc_lower}_` (model refs and source identifiers)
- `raw_apif_vl_` → `raw_apif_{lc_lower}_` (source identifiers)

Use a single sed run per file. Verify one file by hand after running.

### Step 3 — Register the 12 raw sources

In `dbt_project/models/1_staging/api_football/sources.yml`, find the
existing VL block (12 entries: `raw_apif_vl_fixtures_next`, `_leagues`,
`_standings`, `_rounds`, `_teams`, `_transfers`, `_lineups`, `_fixture_events`,
`_fixture_statistics`, `_fixture_players`, `_predictions`, `_players`).

Insert a parallel block immediately AFTER the VL block, with:
- `name`: `raw_apif_{lc_lower}_*`
- `identifier`: `RAW_APIF_{LEAGUE_CODE}_*`
- Same freshness thresholds (`warn_after 30h`, `error_after 54h`)
- Same `loaded_at_field: ingested_at`

### Step 4 — Add UNION ALL blocks to 5 base models

Each base file has a slightly different shape. Match the pattern.

**`dbt_project/models/2_base/api_football/base_apif__teams.sql`** — two
CTEs reference VL. Add a parallel block for the new league in each:
- `stg_teams` CTE: `from {{ ref('stg_apif__{lc_lower}_teams') }}` with `where team_id is not null`
- `stg_fixtures` CTE: `from {{ ref('stg_apif__{lc_lower}_fixtures_next') }}` (no `where`)

**`dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql`** — single
`union all` chain. Add a parallel block after VL:
```sql
union all
select *
from {{ ref('stg_apif__{lc_lower}_fixtures_next') }}
where fixture_id is not null
```

**`dbt_project/models/2_base/api_football/base_apif__leagues.sql`** — single
`union all` chain inside a CTE. Add a parallel block after VL with the full
column list (copy from VL's block, swap the `ref()`).

**`dbt_project/models/2_base/api_football/base_apif__standings.sql`** —
macro-driven. Two changes:
1. In the `{% set standings_union_ctes = [...] %}` list near the top, add
   `'import_stg_{lc_lower}_standings',` after the existing entries.
2. Add an `import_stg_{lc_lower}_standings as (...)` CTE block AFTER the VL
   CTE, BEFORE the `unioned_standings as (...)` CTE. Use the VL block as
   template, swap the `ref()`.

**`dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql`** —
same macro-driven pattern as standings. Two parallel changes:
1. Add `'import_stg_{lc_lower}_fixture_statistics',` to the
   `fixture_statistics_union_ctes` list.
2. Add `import_stg_{lc_lower}_fixture_statistics as (...)` CTE after the
   VL CTE, before `unioned_fixture_statistics`.

### Step 5 — Registry entry

In `docs/competition_registry.yml`, append a new entry AFTER the VL entry
and BEFORE the `# PLANNED` section:

```yaml
  - league_code: "{LEAGUE_CODE}"
    name: "{NAME}"
    country: "{COUNTRY}"
    competition_type: "domestic_league"
    provider: "api_football"
    provider_league_code: null
    provider_league_id: {PROVIDER_LEAGUE_ID}
    season_type: "{SEASON_TYPE}"
    current_season: "{CURRENT_SEASON}"
    history_seasons: {HISTORY_SEASONS}
    status: "active"
    ingest_completeness_gate: soft
    form_source: "league_only"
    raw_table_prefix: "RAW_APIF_{LEAGUE_CODE}"
    api_coverage_verified: "{TODAY_YYYY_MM_DD}"
    notes: "{NOTES}"
```

### Step 6 — Update active competition vars

In `dbt_project/dbt_project.yml`, add `{LEAGUE_CODE}` to
`vars.active_competition_league_codes` in alphabetical order.

### Step 7 — i18n competition labels

In each of `site/i18n/en.json`, `site/i18n/de.json`, `site/i18n/fi.json`,
add a new key to the `competitions` block:

```json
"{LEAGUE_CODE}": "{NAME}"
```

Place it before the `"WC": ...` line (which is by convention the last entry).
Translate the name appropriately for each locale (most domestic-league names
are the same in all three languages).

### Step 8 — Local validation

Run, from the repo root or worktree:

```bash
export PYTHONPATH=.
python scripts/check_registry_var_sync.py
python -c "import json; [json.load(open(f, encoding='utf-8')) for f in ['site/i18n/en.json','site/i18n/de.json','site/i18n/fi.json']]; print('i18n ok')"
```

The first should report `OK (N competitions)` with N having incremented by 1.
The second silently passes if all three JSONs parse cleanly.

### Step 9 — Commit and PR

```bash
git add dbt_project/ docs/competition_registry.yml site/i18n/
git commit --no-verify -m "<message>"
git push origin feat/onboard-{lc_lower}:feat/onboard-{lc_lower} -u
gh pr create --base main --head feat/onboard-{lc_lower} --title "..." --body "..."
```

`--no-verify` is currently needed because the local sqlfluff pre-commit
hook requires dbt to be installed locally with the templater set up. CI runs
sqlfluff against the same files with the full dbt environment and will
validate properly.

The PR body should reference #151 (Wave 1 onboarding) and #121 (parent),
and follow the structure of PR #178 (Liga MX) for consistency.

## Acceptance check after CI

The PR should pass all 5 gate jobs. Specifically:

- `ci-data-build / gate`: must succeed — verifies dbt parse + lint + a full
  dbt build against BigQuery. If this fails, the most likely causes are:
  - A copy-paste typo in one of the staging files (sed-replace skipped a token)
  - A new league_code already present elsewhere
  - sqlfluff lint error from a long line
- `ci-validate / gate`: verifies the registry sync (catches if `league_code`
  was added to the registry but not to `active_competition_league_codes`,
  or vice versa)

## Operational follow-up the user should do

After merge:
1. Re-run the scheduled API-Football ingest. The loader will pick up the new
   league via the registry. If the league's status in the API is "in_progress"
   (mid-season), set `API_FOOTBALL_INCLUDE_IN_PROGRESS=1` in the env.
2. Trigger a dbt build (CI or local) to populate base / core / mart layers.
3. Trigger the pages export workflow to refresh the deployed JSON.
4. Spot-check the deployed `team-season` page for the new league to confirm
   metrics flow end to end.

## Known edge cases

- **VL itself**: do not use this skill to "re-onboard" VL. It's the source
  template; modifying it requires manual edits across all dependent base
  models.
- **WCQ leagues**: shape is different (group-based tournaments); do not use.
- **Long-running campaigns** (e.g. WC qualifiers that span 3 calendar years):
  set `history_seasons` based on the rolling form window the form-source
  dispatch needs, not the API's notion of "current season".
- **Split-season leagues** like Liga MX (Apertura + Clausura in one API
  "season"): API-Football treats both phases as one season. Set
  `season_type: split_year` and `history_seasons: 1`.

## Reference PRs

- PR #178 — Liga MX (LMX) onboarding, the most recent canonical example
- PR (TBD) — first VL-onboarding PR from the registry's git history

## Related issues

- #151 — Wave 1 onboarding tracking (5 leagues)
- #121 — Parent: WC 2026 player coverage
