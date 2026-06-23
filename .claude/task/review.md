# Review — refactor/500-team-season-consolidation — 2026-06-23

diff_sha256: 4863e98a2f29bc6cb259284914d130484b654195468ee39470fab25d1536ce41

## scope-auditor
VERDICT: PASS
risks_checked:
- Grain uniqueness + join safety: `int_team_season__metrics` enforces grain
  (league_code, season_api_year, team_sk) via `unique_combination_of_columns`; `mart_team_season`
  joins on (team_sk, season_sk) to dim_team + standings — deterministic, no row multiplication.
  The impact_map downstream is pasted verbatim `dbt ls` output; the clean_sheets mapping now reads
  `clean_sheets=clean_sheets_sum_season`, matching the code. The §10 Option-A approval is recorded
  in escalations.log (no open decision); the `_season`-column alignment is honestly deferred.
- W/D/L byte-identity under relocation: the counts moved to the rollup via identical
  `countif(result=…)` logic; the pre-existing `wins+draws+losses=played` test (shared.yml) +
  ci-data-build before/after = 0 is the done_when gate that mechanically blocks any regression.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Column EXISTENCE (the earlier build-break): confirmed every `m.<col>` mart_team_season reads is
  in the rollup's FINAL SELECT — `clean_sheets_count_season as clean_sheets_sum_season`
  (int_team_season__metrics line 102) and `m.clean_sheets_sum_season` (mart line 41); the prior
  failure (count computed in a CTE but not exposed) is resolved, and no other column is missing.
- Byte-identity: `goals_against` is non-null at the leg grain (int_legs__team_match filters
  non-null goals), so `countif(goals_against=0)` == old `countif(coalesce(.,0)=0)`; SUM==SUM(coalesce);
  count(distinct fixture_sk)==count(*); W/D/L `result` is accepted_values-tested so the defensive
  upper(trim) is a no-op; team_season_sk surrogate identical. Rename complete (zero stale refs);
  new `_sum_season` columns catalogue-exempt.

## escalations
- question: Was #500 Option A (rename + fold the dedup) approved this session, given memory recorded
  "keep as-is for now" (2026-06-18, metric-layer Phase 1)?
  CPO ANSWER: Approved this session — "Then it's A" + "Rename + fold that dedup"; the 2026-06-18
  parking is superseded. Durable record in `.claude/task/escalations.log` (2026-06-23 entry).
