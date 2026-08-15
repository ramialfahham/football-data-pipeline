# Review — fix/62-leagues-country-json-path — 2026-08-15

diff_sha256: 591b6f9ff24f6471bfffc8180f8f2ca717f8a7b09bc9f8a1c8545610b3055559

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the diff touches `stg_apif__leagues.sql`, `core.yml` and `contract.md`, all listed in
  `scope_paths`; `.claude/active_work.md` is also listed and is excluded from the reviewed patch
  by `review_exclude_paths`, declared in the patch trailer. No out-of-scope file.
- §10/A1 metric-definition risk: this corrects a JSON extraction path
  (`$.league.country` → `$.country.name`, `$.league.flag` → `$.country.flag`), not a metric or a
  formula. The impact_map shows a value-only change with zero downstream consumers of the two
  columns (grep evidence), so no shipped number moves.
- Naming/display (A2): the rendered string for the 21 single-country competitions, and whether
  `mart_competition_index` reads `dim_league.league_country` directly or waits for #69's
  `dim_country`, are both in `decisions_reserved` and are not decided in this diff.
- Prior CPO ruling consistency: verified against `escalations.log` 2026-08-14
  (`feat/62-registry-seed-display-fields`) ruling 3 — the contract's account matches the log, and
  this MR does not reverse it; it fixes the provider-sourced path that ruling already assumed.
- New mechanism / recurring cost: a `not_null` test on an existing column using the model's own
  existing convention (five other columns already tested) is not a new mechanism; no new model,
  table or schedule.
- Credentials: no key/token/password-shaped string anywhere in the diff.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the `stg_apif__leagues.sql` change is a JSON path correction only, still within
  staging's faithful 1:1 flatten allowance per `dbt_project/docs/layering.md` §1_staging — no
  dedup, aggregation or cross-source logic added. `base_apif__leagues.sql` and `dim_league.sql`
  remain pure pass-throughs of the corrected columns.
- Blast radius / A6: independently grepped `league_country|country_flag_url` across
  `4_intermediate/` and `5_marts/` (zero hits) and confirmed the only files touching the columns
  are the staging model, `base_apif__leagues.sql`, `dim_league.sql` and `core.yml` — matching the
  contract. The pasted `dbt ls` lineage was spot-checked by grepping the `ref()` chain and holds.
  The impact_map is real pasted lineage, not an asserted-trivial shortcut.
- Test placement and testing policy: the new `not_null` on `dim_league.league_country`, and the
  deliberate absence of a nullity test on `country_flag_url` (24 international rows carry no
  provider flag, documented in the column description), are consistent with
  `engineering_standards.md` §3. No test was weakened or deleted.
- Catalogue governance and competition-agnosticism: no metric created or redefined — these are
  dimensional attributes, not catalogue metrics — and no hardcoded competition identifier appears.
- Cross-checked the contract's narrative against `escalations.log` ruling 3: the fix corrects
  exactly the extraction bug that ruling's own investigation surfaced, and copy/consumption
  decisions are reserved to the CPO rather than decided here.

## escalations
(none)
