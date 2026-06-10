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

- The competition name and country
- A short league code to assign (e.g. `MLS`, `SPL`, `ED`, `LP`)
- Season type (`split_year` for European-style Aug→May, `calendar_year` for
  spring-autumn or one-year competitions)
- Current season year (e.g. `2025`, `2026`)

**Do NOT accept a `provider_league_id` from the user or from memory.**
The ID must be discovered via a live name-based API search (Step 0b).

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
| `season_type` | `split_year` or `calendar_year` | exact lowercase string |
| `current_season` | `2026` | API season identifier — confirm from Step 0b |
| `history_seasons` | `1` | default 1; bump to 2 if the league's prior season feeds form fallback |
| `confederation` | `CONCACAF` | UEFA / CONMEBOL / CONCACAF / CAF / AFC / OFC / FIFA |
| `tier` | `1` | domestic leagues only; pyramid level (1 = top flight) |
| `slug` | `mls` | stable, locale-independent URL slug — never changes once published |
| `sort_order` | `120` | display order within the competition's group (see registry header) |
| `notes` | free text | rationale, e.g. "WC 2026 host coverage for USA + Canada" |

`provider_league_id` is **not** a user input — it is discovered in Step 0b.

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

### Step 0b — Discover and verify the provider_league_id

**This step is mandatory. Never write a `provider_league_id` sourced from
memory or training data — always discover it from the live API in this session.**

Use `scripts/diagnostics/discover_competition.py` with the correct lookup
parameters for the competition type:

| Competition type | Command |
|---|---|
| Domestic league | `--search "<name>" --country "<nation>" --type league` |
| Domestic cup / super cup | `--search "<name>" --country "<nation>" --type cup` |
| Continental club (UCL, LIBER, etc.) | `--search "<name>" --country World --type cup` |
| International national team (AFCON, Gold Cup, etc.) | `--search "<name>" --country World --type cup` |
| WC qualifiers | `--search "<sub-zone name>" --country World` |

```bash
PYTHONUTF8=1 python scripts/diagnostics/discover_competition.py \
  --search "<competition name>" --country "<country>" --type <league|cup>
```

From the results:
1. **Select the correct row** — verify the name, country, and competition type match
   the intended competition. Be alert to:
   - Youth/women's variants with similar names (e.g. U20 vs senior)
   - Lower-division leagues with similar names (e.g. "National League" England tier 5)
   - Pre/post-rebrand names (verify via `current: true` season year)
2. **Record the ID** from that row as `provider_league_id`
3. **Confirm coverage flags**: `stats_players=True` is required for the player
   insights chain to ever apply to this competition
4. **Confirm active season**: the `season=` value in the output is the current
   active season — use this as `current_season` in the registry entry
5. **Check for collisions**: the script prints `[registry: CODE]` if that ID is
   already assigned. If a collision exists, stop — do not write the entry until
   the collision is resolved.
6. **Verify participant alignment**: for unfamiliar competitions, run a fast spot-check:
   ```bash
   python -c "
   import sys; sys.path.insert(0,'.')
   from ingestion.api_football.settings import get_headers, base_url
   import requests
   r = requests.get(f'{base_url()}/teams', headers=get_headers(),
                    params={'league': <ID>, 'season': <YEAR>}, timeout=30)
   for t in r.json().get('response', [])[:8]:
       print(t['team']['name'])
   "
   ```
   Confirm the returned teams are the expected elite clubs/nations for this competition.

Also confirm `league_code` does NOT already appear in `docs/competition_registry.yml`.

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
    confederation: "{CONFEDERATION}"
    tier: {TIER}                      # domestic_league only — omit for other types
    slug: "{SLUG}"
    sort_order: {SORT_ORDER}
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
PYTHONUTF8=1 python scripts/diagnostics/discover_competition.py --audit {LEAGUE_CODE}
```

- `check_registry_var_sync.py` should report `OK (N competitions)` with N
  having incremented by 1.
- The i18n check silently passes if all three JSONs parse cleanly.
- `discover_competition.py --audit {LEAGUE_CODE}` should print `OK` with no
  `!!!` collision flags. A `---` NAME REVIEW line is acceptable if it is a
  known abbreviation difference; any `!!!` line is a hard stop.

### Step 6 — Commit and PR

```bash
git add docs/competition_registry.yml dbt_project/dbt_project.yml site/i18n/
git commit -m "feat: onboard {LEAGUE_CODE} ({NAME})"
git push origin feat/onboard-{lc_lower} -u
gh pr create --base main --head feat/onboard-{lc_lower} --title "feat: onboard {LEAGUE_CODE} ({NAME})" --body "..."
```

The PR body should record the cost gate answers from Step 0a, the verified
`provider_league_id` (with the search command used to find it), and note that
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
3. **Verify ingest health** with the `verify-competition-ingest` skill once the
   first ingest + build have completed:

   ```bash
   PYTHONUTF8=1 python scripts/diagnostics/verify_competition_ingest.py --league {LEAGUE_CODE} --strict
   ```

   This catches the three defect classes that have each reached production —
   NULL `fixture_id` (#297), stale wrong-ID fixture-details rows (#296), and
   teams missing from `dim_team` — before they surface downstream. A clean
   `--strict` run (exit 0) is the gate for considering the competition healthy.
   Triage any `!!` finding per the verify-competition-ingest skill before moving on.
4. Trigger the pages export workflow to refresh the deployed JSON.
5. Spot-check the deployed fixture list for the new league to confirm data
   flows end to end.

## Known edge cases

- **WCQ leagues**: shape is different (group-based tournaments); do not use this skill.
- **Long-running campaigns** (e.g. qualifiers spanning 3 calendar years):
  set `history_seasons` based on the rolling form window needed, not the API's
  notion of "current season".
- **Split-season leagues** like Liga MX (Apertura + Clausura in one API
  "season"): set `season_type: split_year` and `history_seasons: 1`.
- **Qualifying phases** (UCL/UEL/UECL qualifying, Libertadores preliminary):
  these are NOT separate competitions in the API — they are rounds within the
  main competition's `league_id`. No separate registry entry is needed.

## Related issues

- #277 — Path B skill rewrite
- #292 — Competition ID audit (root cause of the procedure tightening)
- #258–#262 — Onboarding waves
