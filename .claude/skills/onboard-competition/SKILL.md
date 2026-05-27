---
name: onboard-competition
description: |
  Onboard a new football competition (domestic league or tournament) into the
  football-data-pipeline. Under Path B (unified raw tables) this requires zero
  SQL file changes — only a registry entry, a dbt vars sync, and i18n labels.
  Generic staging models surface the new league_code automatically.

  Use this when a new league_code needs to be onboarded. Do NOT use for WC
  qualifier competitions (WCQ*) — those are pre-onboarded with tournament-
  specific mart overlays.
---

# onboard-competition

Under Path B all competitions share unified raw tables (`RAW_APIF_{entity}`),
discriminated by a `league_code STRING` column. Adding a competition requires
**zero SQL file edits** — no staging files, no source YAML, no base model
changes. The registry entry is the entire change.

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
  those carry tournament-specific mart overlays. Do not run this skill against
  those codes.
- Renaming an existing league. That's a separate workflow involving snapshot
  history migration.

## Required inputs (collect before starting)

| Input | Example | Validation |
|---|---|---|
| `league_code` | `MLS` | 2–6 uppercase letters/digits, unique vs `docs/competition_registry.yml` |
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

Record the answers in the PR description. The registry entry (`Step 2`) must
reflect the agreed `ingest_active` value.

### Step 0b — Validate technical inputs

- Confirm `provider_league_id` against the live API: `GET /leagues?id={id}`
  should return that league. The response's `coverage.fixtures.statistics_players`
  must be `true` for the player insights work to ever apply.
- Confirm `league_code` does NOT already appear in `docs/competition_registry.yml`.

### Step 1 — Branch from origin/main

```bash
git fetch origin main --quiet
git checkout -B feat/onboard-{league_code_lower} origin/main
```

### Step 2 — Registry entry

In `docs/competition_registry.yml`, append a new entry in the appropriate
status section (`ACTIVE` or `IN PROGRESS`):

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
    api_coverage_verified: "{TODAY_YYYY_MM_DD}"
    notes: "{NOTES}"
```

**Do NOT add a `raw_table_prefix` field.** All competitions write to the
unified raw tables (`RAW_APIF_{entity}`). The ingestion loader reads the
registry at startup and populates `league_code` automatically.

### Step 3 — Sync active competition vars

```bash
python scripts/sync_dbt_vars.py
```

This rewrites `active_competition_league_codes` in `dbt_project/dbt_project.yml`.
Do NOT edit `dbt_project.yml` by hand — `check_registry_var_sync.py` in CI
enforces that the two files match exactly.

### Step 4 — i18n competition labels

In each of `site/i18n/en.json`, `site/i18n/de.json`, `site/i18n/fi.json`,
add a new key to the `competitions` block:

```json
"{LEAGUE_CODE}": "{NAME}"
```

Place it before the `"WC": ...` line (which is by convention the last entry).
Translate the name appropriately for each locale (most domestic-league names
are the same in all three languages).

### Step 5 — Local validation

```bash
python scripts/check_registry_var_sync.py
python -c "import json; [json.load(open(f, encoding='utf-8')) for f in ['site/i18n/en.json','site/i18n/de.json','site/i18n/fi.json']]; print('i18n ok')"
```

`check_registry_var_sync.py` should report `OK (N competitions)` with N
having incremented by 1. The i18n check silently passes if all three
JSONs parse cleanly.

### Step 6 — Commit and PR

```bash
git add docs/competition_registry.yml dbt_project/dbt_project.yml site/i18n/
git commit -m "feat: onboard {LEAGUE_CODE} ({NAME})"
git push origin feat/onboard-{lc_lower} -u
gh pr create --base main --head feat/onboard-{lc_lower} --title "feat: onboard {LEAGUE_CODE} ({NAME})" --body "..."
```

The PR body should record the cost gate answers from Step 0a and note that
no SQL files were added (zero-file rule).

## Acceptance check after CI

- `ci-validate / validate`: runs `check_registry_var_sync.py` and `check_layer_contract.py`.
  The layer contract check will **fail** if any per-competition staging subdirectory
  exists — do not create any files under `dbt_project/models/1_staging/api_football/`.
- `ci-data-build / data-build`: dbt build against BigQuery. The new `league_code`
  flows through all generic staging and base models automatically — no model
  changes required.

## Operational follow-up after merge

1. The scheduled ingest picks up the new league via the registry automatically.
   If `ingest_active: false`, flip it to `true` when ready and push a follow-up
   commit (no PR needed for that single-field change).
2. Trigger a dbt build (CI or local) to populate base / core / mart layers.
3. Trigger the pages export workflow to refresh the deployed JSON.
4. Spot-check the deployed fixture list for the new league to confirm data
   flows end to end.

## Known edge cases

- **WCQ leagues**: shape is different (group-based tournaments); do not use this skill.
- **Long-running campaigns** (e.g. qualifiers spanning 3 calendar years):
  set `history_seasons` based on the rolling form window needed, not the API's
  notion of "current season".
- **Split-season leagues** like Liga MX (Apertura + Clausura in one API
  "season"): set `season_type: split_year` and `history_seasons: 1`.

## Related issues

- #277 — Path B skill rewrite (this update)
- #258–#262 — Wave 2 onboarding (first competitions using this procedure)
