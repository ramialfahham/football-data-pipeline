---
name: verify-competition-ingest
description: |
  Verify the ingest health of one competition (or the whole platform) after
  onboarding, after a provider_league_id correction, or whenever a dbt
  relationship test fails on team/fixture keys. Detects the three data defects
  that have each reached production — NULL fixture_id, stale wrong-ID
  fixture-details rows, and teams missing from dim_team — plus a coverage sanity
  pass. Read-only by default; points at the existing remediation scripts.

  Use this as the post-merge gate referenced by the onboard-competition skill.
---

# verify-competition-ingest

A competition can pass CI and still carry latent data defects that only surface
days later as a failing relationship test or an empty UI panel. This skill runs
the four checks that correspond to defects already seen in production, so they
are caught at the raw/source layer instead of four layers downstream.

## When to use

- **After onboarding** a new `league_code` (the operational follow-up step of
  `onboard-competition`).
- **After correcting a `provider_league_id`** (a wrong ID leaves stale rows that
  WRITE_APPEND never removes).
- **When a dbt relationship test fails** on `*.team_sk → dim_team` or on a
  fixture key — this skill localises the cause fast.
- **Ad hoc**, to audit the whole platform's ingest health.

## What it checks

The backing script is `scripts/diagnostics/verify_competition_ingest.py`. Every
check is registry-driven and competition-agnostic (keyed on `league_code`).

| # | Check | Defect class | Layer read | Remediation |
|---|-------|--------------|-----------|-------------|
| 1 | NULL `fixture_id` while payload has `$.fixture.id` | bug #297 | `raw.RAW_APIF_FIXTURE_DETAILS` | `backfill_fixture_ids.py` |
| 2 | Payload `$.league.id` ≠ registry `provider_league_id` | bug #296 | `raw.RAW_APIF_FIXTURE_DETAILS` | `purge_stale_fixture_details.py` |
| 3 | `team_sk` in `fct_fixture_team_stats` / `fct_standings` absent from `dim_team` | Inter Miami / GCUP class | `core.*` | fix team source (e.g. `base_apif__teams` coverage) or full-refresh the stale incremental fact |
| 4 | Fixture-details row counts, distinct seasons, current_season represented | coverage sanity | `raw.RAW_APIF_FIXTURE_DETAILS` | investigate ingest if an active league has data but the wrong seasons |

Checks 1, 2 and 4 read raw only and work before dbt has built. Check 3 reads the
modeled `core` dataset and is **skipped** (with a notice, not a pass) if those
tables don't exist yet.

### Severity model

- `!!` — an **unambiguous defect** (checks 1–3). Counts toward the problem total
  and trips `--strict`.
- `~`  — a **soft notice** (check 4): zero finished fixtures for a not-yet-started
  tournament, or current_season not yet represented (pre-season). Expected in
  many valid states, so it does **not** trip `--strict`.
- `OK` — healthy.

## Procedure

### Step 1 — Run the verifier

For a single competition (typical post-onboarding use):

```bash
PYTHONUTF8=1 python scripts/diagnostics/verify_competition_ingest.py --league {LEAGUE_CODE}
```

For the whole platform:

```bash
PYTHONUTF8=1 python scripts/diagnostics/verify_competition_ingest.py
```

Add `--strict` to make it exit non-zero on any `!!` defect (use in gating
contexts; without it the script is report-only and always exits 0).

### Step 2 — Triage findings

- **Check 1 `!!` (NULL fixture_id):** run `python scripts/diagnostics/backfill_fixture_ids.py`
  (dry-run first with `--dry-run`). Idempotent. New NULLs after a known-good
  date mean an ingest ran on pre-#298 code — confirm the deployed loader is current.
- **Check 2 `!!` (stale league.id):** run
  `python scripts/diagnostics/purge_stale_fixture_details.py` (dry-run first).
  This means a `provider_league_id` was corrected and the old competition's rows
  are orphaned under the same `league_code`.
- **Check 3 `!!` (orphaned team_sk):**
  - If the team genuinely exists (appears in standings/fixtures) but not in
    `dim_team`, it's a **team-source coverage gap** — fix in `base_apif__teams`
    (the model already unions teams endpoint + fixtures + standings).
  - If the orphan is a stale team from a wrong ID that the source no longer
    contains, it's a **stuck incremental ghost** — `dbt run --full-refresh
    --select <fact_model>` drops it (incremental MERGE never deletes rows).
    Confirm by checking whether the team still exists in the model's source view.
- **Check 4 `~`:** usually benign. Only act if an active competition that should
  have finished matches shows 0 rows, or shows only stale seasons.

### Step 3 — Re-verify

After any remediation, re-run Step 1 (with `--strict`) and confirm a clean
report before considering the competition healthy.

## Notes

- The script never writes data. All remediation is delegated to the dedicated,
  idempotent diagnostic scripts so each fix is auditable and dry-runnable.
- Dataset names follow the project convention that each dbt layer name is its
  BigQuery dataset (`raw`, `core`, …); see `macros/generate_schema_name.sql`.

## Related

- `onboard-competition` — references this skill as its post-merge gate.
- `scripts/diagnostics/backfill_fixture_ids.py` (#297)
- `scripts/diagnostics/purge_stale_fixture_details.py` (#296)
