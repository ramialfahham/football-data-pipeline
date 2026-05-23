---
name: onboard-competition
description: |
  Onboard a new football competition (domestic league or tournament) into the
  football-data-pipeline. Scaffolds 12 dbt staging models, registers sources,
  updates the competition registry, runs sync_dbt_vars.py to derive the
  active-competition-codes var, and adds the i18n competition label in en/de/fi.
  Base models auto-discover the new league via Jinja loops — no SQL edits needed.

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

### Step 0a — Cost gate (answer before any file is written)

Ask the user these three questions and record the answers. Do not proceed
to Step 0b until all three are answered.

1. **`ingest_active`** — should ingestion start immediately when this PR merges,
   or should it be paused until you're ready? (`true` / `false`)
2. **`history_seasons` rationale** — the required value is already in the inputs,
   but state explicitly why: is this current-season-only, or does it include a
   prior season for form fallback? One sentence.
3. **Endpoint scope** — does this competition need the full fanout (lineups, events,
   statistics, fixture players, predictions) at launch, or only the cheap phases
   (fixtures, standings, teams, rounds)? Note: full fanout dominates API quota.

Record the answers in the PR description. The registry entry (`Step 5`) must
reflect the agreed `ingest_active` value.

### Step 0b — Validate technical inputs

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

### Step 4 — Registry entry

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
    ingest_active: {INGEST_ACTIVE}
    ingest_completeness_gate: soft
    form_source: "league_only"
    raw_table_prefix: "RAW_APIF_{LEAGUE_CODE}"
    api_coverage_verified: "{TODAY_YYYY_MM_DD}"
    notes: "{NOTES}"
```

### Step 5 — Sync active competition vars

Run from the repo root:

```bash
python scripts/sync_dbt_vars.py
```

This reads `docs/competition_registry.yml` and rewrites the
`active_competition_league_codes` list in `dbt_project/dbt_project.yml`
automatically. Do NOT edit `dbt_project.yml` by hand — `check_registry_var_sync.py`
in CI enforces that the two files match exactly.

### Step 6 — i18n competition labels

In each of `site/i18n/en.json`, `site/i18n/de.json`, `site/i18n/fi.json`,
add a new key to the `competitions` block:

```json
"{LEAGUE_CODE}": "{NAME}"
```

Place it before the `"WC": ...` line (which is by convention the last entry).
Translate the name appropriately for each locale (most domestic-league names
are the same in all three languages).

### Step 7 — Local validation

Run, from the repo root or worktree:

```bash
export PYTHONPATH=.
python scripts/check_registry_var_sync.py
python scripts/check_base_model_no_hardcoded_leagues.py
python -c "import json; [json.load(open(f, encoding='utf-8')) for f in ['site/i18n/en.json','site/i18n/de.json','site/i18n/fi.json']]; print('i18n ok')"
```

`check_registry_var_sync.py` should report `OK (N competitions)` with N
having incremented by 1. `check_base_model_no_hardcoded_leagues.py` should
report OK — it will if the new staging models were created correctly and no
hardcoded refs were introduced. The i18n check silently passes if all three
JSONs parse cleanly.

### Step 8 — Commit and PR

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
- `ci-validate / gate`: runs three checks:
  - `check_registry_var_sync.py` — fails if registry and `active_competition_league_codes` diverge
  - `check_base_model_no_hardcoded_leagues.py` — fails if any cross-league base model
    contains a hardcoded `ref('stg_apif__XX_...')` instead of using the Jinja loop
  - `dbt parse` — catches model compilation errors

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
  template for staging files. The base models are Jinja-loop-driven and
  need no edits when adding any league including VL variants.
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
