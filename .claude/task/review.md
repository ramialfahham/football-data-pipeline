# Review — feat/69-5-62-3-country-fk-and-mart — 2026-08-17

diff_sha256: 60458ded2e3baba86e948a9ebc8e55fc13dd5cf7ce71a3074b1695bfcf118de0

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Traced every ordering/region_rank citation in mart_competition_index.sql, shared.yml,
  confederations.csv and schema.yml back to the new 2026-08-16 escalations.log entry (lines
  3432-3477) — quoted rulings 1-4 match the code's claims exactly (sort_order obsolete, the
  sort-key sequence, region_rank's 1-7 values, mart-carries-facts/spec-declares-order-by),
  resolving round-1's finding (an issue note cited as authority instead of this log).
- Checked contract.md's decisions_taken for any residual unbacked authority claim on
  ordering/region_rank — found none; it restricts itself to the country-FK/region_label decision,
  backed by prior #69 quotes already in escalations.log.
- Swept the full cumulative patch for credential-shaped strings and widened permissions — none
  found.
- Confirmed every file touched in the diff is listed in contract.md's scope_paths, and that the
  country-override join pattern added to the four base models is the same seed+join+coalesce
  mechanism already approved for team_name_overrides (no new mechanism), consistent with
  decisions_taken's "NEW MECHANISM: none" claim.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- dbt_project/seeds/schema.yml lines 112-122: region_rank now has a schema entry with not_null +
  unique tests, matching sibling-column coverage in the same seed (round-1 finding closed).
- dbt_project/seeds/confederations.csv values (UEFA=1...OFC=7) cross-checked against
  .claude/task/escalations.log's 2026-08-16 Ruling 3 — match exactly.
- dbt_project/seeds/schema.yml line 84 confederations description no longer claims "ADDITIVE AND
  NOT YET READ"; now correctly names mart_competition_index as reader (round-1 secondary note
  closed).
- mart_competition_index.sql (region_rank selected as a bare fact, no pre-baked ORDER BY) and
  shared.yml (region_rank column test/description) checked for consistency with the seed-side fix
  — consistent.
- Full review_input.patch file list re-scanned to confirm the round-2 delta touched only
  dbt_project/seeds/schema.yml and .claude/task/escalations.log beyond the round-1 diff — no
  unreviewed surface introduced.
- region_rank change checked against catalogue-governance (A1): not a metric_catalogue row, so no
  catalogue-row requirement applies.
- (Round 1, still standing — delta did not touch these): layer placement of the country-override
  join in base (feedback_entity_corrections_in_base pattern, matches the existing
  team_name_overrides precedent in the same two files); mart_competition_index reads only core
  dims/seeds, no staging/raw refs; single_country removal complete and consistent across
  competition_types.csv and its schema.yml test block; new relationships tests on the four country
  columns correctly permit NULL, matching the "can be NULL" column docs.

## escalations
(none)
