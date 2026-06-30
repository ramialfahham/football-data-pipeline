# Review — feat/391-gap01-team-venue — 2026-06-30

> G3 Lock artifact. #391 GAP-01 — team founded year + venue (name/city/capacity) on the v2 team profile.
> Additive mart columns (from the existing dim_team join) + export reshape + folded wireframe/register
> doc-sync. Required set (routing): scope-auditor (always) + analytics-engineer (dbt_project/**) + cto
> (scripts/export_*.py + tests/**) + bi-analyst (docs/wireframes/**). All four fresh at this hash.

diff_sha256: 191bcd337f9b92776c060ca502ca8adbb050d60ee33c9327a54f7d2c248a7fa9

## scope-auditor
VERDICT: PASS
risks_checked:
- Partial venue-data null-handling: _venue_block returns None only when ALL of name/city/capacity are null, and a block (with the known fields + nulls) when partial — honest partial presence, mirrors the GAP-16 current_team pattern; the all-null path is tested. Boundary holds (no defect).
- Identity-column stripping: the 4 new columns are added to _strip_identity's drop-set (export_site_data.py) and the test asserts they do not leak into per-season rows (team_founded_year/venue_name not in seasons[0]). Correct + tested.
NON-BLOCKING NOTE (recorded, not corrected — see header rationale): the contract lists PAYLOAD SHAPE
  (and the doc-sync FOLD) under decisions_reserved, but the CPO confirmed both at plan approval
  (ExitPlanMode) — so they are properly decisions_taken. The reserved text already documents the
  plan-approval confirmation ("CPO confirms at ExitPlanMode" / "the CPO's call at plan approval"), so it
  is honest, just placed under the wrong heading. contract.md is ephemeral per-task scratch (overwritten
  next task); a full re-review cycle to relocate two bullets is disproportionate. Flagged to the CPO.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- dim_team column availability + no fan-out: dim_team.sql:13-19 carries team_founded_year + venue_name/city/capacity; the `teams` CTE is `select * from dim_team` so no CTE change; the join (m.team_sk = t.team_sk) is unchanged — only 4 more columns selected in the identity block. No grain change.
- Drift-guard scope: assert_no_uncatalogued_season_metric targets only int_team_season__metrics + int_player_season__metrics — mart_team_profile identity columns are not catalogue-gated; no spurious drift failure.
- Consumption-layer + DQ: _venue_block is pure reshape (select + serialize, no math/window/affiliation); _strip_identity drops the 4 from per-season rows; no not_null on sparse nullable identity is correct per the CPO ruling; the (team_sk, season_sk) grain test is untouched. (Non-defect: a partial-null venue returns a block with the known fields — preferable to dropping a known name.)

## cto-reviewer
VERDICT: PASS
risks_checked:
- Top-level isolation from _strip_identity: founded_year + _venue_block(latest) are built from `latest` independently of the per-season strip loop; adding the 4 fields to _strip_identity removes them only from season rows, never from the top-level block. Provably independent.
- Test adequacy + no regression: the extended team test asserts founded_year + the venue block + that they are stripped from seasons (all would fail pre-patch: the old return had no founded_year/venue key and the old drop-set lacked the 4 fields); the absence test would KeyError pre-patch; no test does exact top-level dict-equality on the team payload (additive keys = zero regression). Export wired into no workflow (live MVP via export_pages_data.py only); no new import/dependency/cost.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Field-binding accuracy across mart → export → wireframe: dim_team columns → mart_team_profile.sql:70-73 → _venue_block + latest.get("team_founded_year") → payload `founded_year` + `venue`{name,city,capacity}; matches wireframe §3 enumeration + §5 binding exactly; key names correctly transformed (team_founded_year → founded_year; venue_* → nested venue block). The brief §6.2 promises exactly these identity fields.
- Locked display contract untouched: metrics_display.md not in the diff; the 16-row team SEASON METRICS list (§8) unchanged; founded/venue are identity (no tier/group/order, no catalogue entry); the §4 ASCII edit only notes data-in-payload, no display treatment invented. GAP-01 cleanly closed in §10 + register (format consistent with GAP-14/16); the stale GAP-15 §10 line is a pre-existing entry correctly left out of this PR's scope.

## escalations
(none) — all four required reviewers PASS at this hash; no FAIL, no ESCALATE. The field-set ruling, the
payload shape, and the doc-sync fold were CPO-directed this session (disposition ruling + plan approval),
recorded as such. The scope-auditor's contract-heading hygiene note is recorded above (non-blocking).
