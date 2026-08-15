# Review — fix/62-standardize-country-names — 2026-08-15

diff_sha256: 9fe213cf246da05581fc071319f7fb4b0ea4acd8b1a0b8b80049d820dd6411f5

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- The diff's file set matches `scope_paths` exactly — `seeds/country_name_overrides.csv`,
  `seeds/schema.yml`, `base_apif__leagues.sql`, `base.yml`, the new singular test, and
  `active_work.md`. No out-of-scope file touched.
- The cited CPO ruling exists verbatim in `.claude/task/escalations.log` (2026-08-14: "Our
  transformation layer is the place where we clean, reconcile and standardize the data... Raw
  doesn't define the taxonomies"), so the claimed authority for standardizing in base is real.
- Checked for scope creep into the other country columns (`dim_team.team_country`,
  `dim_player.player_birth_country`, `dim_coach.coach_birth_country`): the diff touches only
  `league_country`, `decisions_reserved` excludes the other three explicitly, and no teams,
  players or coaches file appears in the patch.
- Checked whether this is a NEW mechanism needing fresh authority: `team_name_overrides` (seed +
  left join + coalesce + `assert_..._still_needed`) already exists in `base_apif__teams_global.sql`.
  This is a literal reapplication of that pattern to a second column, so A3 does not apply.
- Verified `dim_league.sql` still passes `league_country` through unmodified and `core.yml` adds no
  coalesce — base corrects, the core dim publishes.
- The one genuinely reserved §10 item (`USA` -> "United States of America") is flagged as a CPO copy
  decision in `decisions_taken` and in the seed's `source`/`note`, not silently taken.
- Swept the patch for credential-shaped strings — none.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the correction lives in `base_apif__leagues.sql` via seed + `left join` +
  `coalesce`, matching `layering.md` §2_base, and keeps country an ATTRIBUTE rather than promoting
  it to a dim before a rollup consumer exists. `dim_league.sql` is confirmed unchanged — still a
  bare `select league_country` pass-through — so core publishes rather than corrects, per
  `feedback_entity_corrections_in_base`. No hardcoded `league_code` in the new SQL.
- Fidelity to the existing pattern: compared `base_apif__teams_global.sql:12-52` against the new
  `base_apif__leagues.sql:1-44` — same three-part shape. The one structural divergence, keying on a
  provider STRING rather than a stable numeric id and adding a "provider string disappeared" branch
  to the test, is forced by the absence of a country dim today, is stated explicitly in both the
  seed description and `decisions_reserved`, and is a SUPERSET of the team test's coverage, not a gap.
- The test can actually fail: it fires when the override equals the provider string (no-op row) or
  when the provider string no longer appears in `stg_apif__leagues.country` at all. Checked all 3
  seed rows against both conditions — green today with a demonstrable path to red, not decoration.
- Grain safety: `provider_country` carries a `unique` test, so the new `left join` cannot fan out
  rows and the model's existing `unique_combination_of_columns` grain test still holds.
- Catalogue, consumption and config-as-code: not a metric, no export script touched, no
  `dbt_project.yml` change, no per-model materialization override — A1/A5 do not apply.
- Residual-gap honesty: the seed's schema entry states plainly that a newly onboarded hyphenated
  country is NOT caught by this mapping and closes only with #69's FK, rather than implying full
  coverage.

## escalations
(none)
