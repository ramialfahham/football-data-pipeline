# Review — feat/team-yoy-all-metrics — 2026-07-12

> Extend team YoY to ALL season metrics, matchday-aligned (Option A / COMPOSE). Round 5.
> History: R1 diff PASSED but ci-data-build's new cumulative ratio test failed on one provider-noise
> row (danger_zone_ratio 1.25 — fixture 1149592 has shots_inside_box 5 > shots_total 4). R3 split the
> cumulative ratio test by invariant family; the AE reviewer correctly FAILED it because the same
> over-strict bound survived in the composed-YoY test. R4 split that too — both reviewers PASSED
> (c0ad071f) — but ci-data-build THEN failed to BUILD int_team_season__metrics: "team_sk is
> ambiguous". Root cause: the projection's final SELECT joins season_final (sf) to a matchdays CTE
> (md) that also exposes team_sk, so the unqualified team_sk inside generate_surrogate_key was
> ambiguous. It was MASKED in R1–R3 because the upstream cumulative test failure skipped building the
> whole downstream (the projection + its direct consumer mart_team_profile never ran). R5 fix = ONE
> line: qualify the surrogate-key inputs to sf.team_sk / sf.season_sk. Verified against BigQuery:
> `bq --dry_run` of the full projection AND the new int_team_profile__yoy both "successfully
> validated"; every mart y.<col> confirmed present in the YoY output. Required reviewers for
> `dbt_project/**`: scope-auditor (always) + analytics-engineer-reviewer. Both PASS.
> dbt CLI broken locally — ci-data-build is the executable gate.

diff_sha256: b90f02d3674754f94b9aaf88dd98008631b187cf1b10289ad6d15a8b4b9d8959

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the one-line change is inside int_team_season__metrics.sql (already in scope); staged diff
  still touches ONLY the authorized set (4 dbt models + 3 yml + contract.md). Nothing new out of scope.
- §10: qualifying ['team_sk','season_sk'] → ['sf.team_sk','sf.season_sk'] is a pure SQL correctness
  fix — no metric formula / catalogue / displayed-number / naming / mechanism change.
- Contract honesty: byte-identity claim unaffected (identical surrogate hash); contract not edited
  this round, correctly (the fix introduces no new decision to document).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Ambiguity source + fix completeness: confirmed team_sk is genuinely dual-sourced (sf via
  season_final = select * from cumulative; AND md = the int_legs__team_match distinct-round CTE which
  selects team_sk/league_code/season_api_year/season_matchdays_used). season_sk is NOT in md (only sf),
  so qualifying it too is harmless. No other bare/unqualified reference remains: sf.* except(match_number)
  is a scoped wildcard, md.season_matchdays_used qualified, ON clause fully qualified.
- Byte-identity of team_season_sk: traced team_sk/season_sk as unmodified passthrough
  (int_team_season_record → cumulative → sf); the row picked by qualify order by match_number desc is
  provably the same physical row as the old kickoff desc/fixture_sk desc (match_number = row_number
  over that exact order). Qualification changes column resolution scope, not the value fed to the hash
  → team_season_sk identical.
- Never-before-built downstream swept: read int_team_profile__yoy + mart_team_profile end-to-end — every
  reference alias-qualified or single-source, no analogous dual-source-bare-name pattern; cross-checked
  all 62 mart y.<col> against the YoY's 62 outputs (1:1). Refinement: the genuinely-unverified node was
  mart_team_profile (direct ref to the projection), not the YoY (which refs only the cumulative model).
- Re-derived the int_team_season__metrics consumer list via grep — exact match to the contract's six.
  Formula-move verbatim (no metric redefinition); no hardcoded league; matchdays/season_final are
  1-row-per-team-season so the projection join is 1:1 (no fan-out).

## escalations
(none)
